from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from werkzeug.security import generate_password_hash
from . import db
import pandas as pd
from dateutil.parser import parse
from sklearn.preprocessing import LabelBinarizer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import numpy as np

bp = Blueprint("views", __name__)
K = 9  # optimal k for kmeans


@bp.route('/', methods=['GET'])
def home():
    return render_template("home.html")


@bp.route('/one_user_history', methods=['GET'])
def one_user_history():
    cursor = db.histories.find({'email': session['email']})
    return render_template('one_user_history.html', cursor=cursor)


@bp.route('/modify_one_user_profile', methods=['GET', 'POST'])
def modify_one_user_profile():
    if request.method == 'POST':
        fullName = request.form.get('fullName')
        nationality = request.form.get('nationality')
        password = request.form.get('password')
        age = request.form.get('age')
        gender = request.form.get('gender')
        budget_accommodation = request.form.get('budget_accommodation')
        budget_transportation = request.form.get('budget_transportation')
        if len(fullName) < 2:
            flash('full name must be greater than 1 characters.', category='error')
        elif len(nationality) < 3:
            flash('nationality must be greater than 2 characters.', category='error')
        elif len(password) < 7:
            flash('passwords must be greater than 6 characters.', category='error')
        elif int(age) < 0:
            flash('age must be great than 0.', category='error')
        elif not (gender in ('Male', 'Female')):
            flash('gender must be Male or Female.', category='error')
        elif int(budget_accommodation) < 0:
            flash('budget must be greater than 0.', category='error')
        elif int(budget_transportation) < 0:
            flash('budget must be greater than 0.', category='error')
        else:
            # update user document
            myquery = db.users.find_one({'email': session['email']})
            new_password = password
            if myquery.get('password', None) != password:  # user changes password
                new_password = generate_password_hash(password)
            new_document = {
                "$set": {"fullName": fullName,
                         "nationality": nationality,
                         'password': new_password,
                         'age': age,
                         'gender': gender,
                         'budget_accommodation': budget_accommodation,
                         'budget_transportation': budget_transportation}
            }
            db.users.update_one(myquery, new_document)
            flash('Profile modified successfully.', category='success')
            return redirect(url_for('views.home'))
    return render_template('/modify_one_user_profile.html', user_found=db.users.find_one({'email': session['email']}))


@bp.route('/get_recommendation_list', methods=['GET'])
def get_recommendation_list():
    # create df1 [email, age, gender, nationality, budget_accommodation, budget_transportation]
    df1 = pd.DataFrame(list(db.users.find()))
    df1 = df1.drop(['_id', 'fullName', 'password'], axis=1)
    df1 = df1.dropna(axis=0,
                     how='any')  # some users may not add their nationality, budget_transportation, or budget accommodation
    df1[["age", "budget_transportation", "budget_accommodation"]] = df1[
        ["age", "budget_transportation", "budget_accommodation"]].apply(pd.to_numeric)

    # create df2 [emai, destination]
    df2 = pd.DataFrame(list(db.histories.find()))

    df2 = df2[['email', 'destination', 'end_date']]

    # only keep the latest travel history of a user. latest means has the biggest end_date
    df_email = df2[['email']]

    df_email = df_email[df_email.duplicated(keep=False)]
    index_candidate = df_email.groupby(list(df_email)).apply(lambda x: tuple(x.index)).tolist()
    index_save = []
    for tuple_element in index_candidate:  # for each tuple, they have same emails
        index_latest = tuple_element[0]
        for index in tuple_element:
            if parse(df2.iloc[index]['end_date']) > parse(df2.iloc[index_latest]['end_date']):
                index_latest = index
        index_save.append(index_latest)
    index_all_candidate = []
    for e in index_candidate:
        for f in e:
            index_all_candidate.append(f)
    index_to_be_deleted = list(set(index_all_candidate) - set(index_save))
    df2 = df2.drop(index_to_be_deleted)
    df2 = df2.drop(['end_date'], axis=1)  # now each only has one travel history remaining

    # merge those 2 dataframes
    df = df1.merge(df2, how='inner', on='email')

    # normalize age, accommodation cost, transportation cost
    def get_scaler_and_column_number(df, column_name):
        column_number = df[column_name].values.reshape(-1, 1)
        scaler_number = StandardScaler()
        new_column = scaler_number.fit_transform(column_number)
        return scaler_number, new_column

    # one hot gender, nationality
    def get_scaler_and_column_str(df, column_name):
        column_str = df[column_name]
        scaler_str = LabelBinarizer()
        new_column = scaler_str.fit_transform(column_str)
        return scaler_str, new_column

    def return_kmeans_scaler_groupdct(df):
        scaler_age, column_age = get_scaler_and_column_number(df, 'age')
        scaler_accommodation, column_accommodation = get_scaler_and_column_number(df, 'budget_accommodation')
        scaler_transportation, column_transportation = get_scaler_and_column_number(df, 'budget_transportation')
        scaler_gender, column_gender = get_scaler_and_column_str(df, 'gender')
        scaler_nationality, column_nationality = get_scaler_and_column_str(df, 'nationality')

        nd_array_all_5attributes = np.concatenate(
            (column_age, column_gender, column_nationality, column_accommodation, column_transportation), axis=1)

        kmeans = KMeans(init='k-means++', n_clusters=9, random_state=0, n_init=1).fit(nd_array_all_5attributes)

        group_no = kmeans.labels_.reshape(-1, 1)
        destination_column = df['destination'].to_numpy().reshape(-1, 1)

        array_destination_group = np.concatenate((destination_column, group_no), axis=1)
        group_dct = {}
        for i in range(K):
            group_dct[i] = []
        for i in range(len(array_destination_group)):
            current_group = array_destination_group[i, 1]
            current_destination = array_destination_group[i, 0]
            group_dct[current_group].append(current_destination)
        for i in range(K):
            destination_list = group_dct[i]
            dict_temp = {}
            for key in destination_list:
                dict_temp[key] = dict_temp.get(key, 0) + 1
            sorted_destinations = sorted(dict_temp.items(), key=lambda x: x[1], reverse=True)
            group_dct[i] = sorted_destinations
        return kmeans, scaler_age, scaler_gender, scaler_nationality, scaler_accommodation, scaler_transportation, group_dct

    kmeans, scaler_age, scaler_gender, scaler_nationality, scaler_accommodation, scaler_transportation, group_dct = return_kmeans_scaler_groupdct(
        df)
    df_new_customer1 = pd.DataFrame(list(db.users.find({'email': session['email']})))

    column_age = df_new_customer1['age'].values.reshape(-1, 1)
    column_age = scaler_age.transform(column_age)

    column_gender = df_new_customer1['gender']
    column_gender = scaler_gender.transform(column_gender)

    column_nationality = df_new_customer1['nationality']
    column_nationality = scaler_nationality.transform(column_nationality)

    column_accommodation = df_new_customer1['budget_accommodation'].values.reshape(-1, 1)
    column_accommodation = scaler_accommodation.transform(column_accommodation)

    column_transportation = df_new_customer1['budget_transportation'].values.reshape(-1, 1)
    column_transportation = scaler_transportation.transform(column_transportation)

    ndarray_new_customer1 = np.concatenate(
        (column_age, column_gender, column_nationality, column_accommodation, column_transportation), axis=1)
    group_of_new_customer1 = kmeans.predict(ndarray_new_customer1).item()
    recommendation_list = group_dct[group_of_new_customer1]
    return render_template('/get_recommendation_list.html', recommendation_list=recommendation_list)


@bp.route('/book_travel', methods=['GET', 'POST'])
def book_travel():
    if request.method == 'POST':
        destination = request.form.get('destination')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        accommodation_type = request.form.get('accommodation_type')
        accommodation_cost = request.form.get('accommodation_cost')
        transportation_type = request.form.get('transportation_type')
        transportation_cost = request.form.get('transportation_cost')
        if len(destination) < 2:
            flash('destination must be greater than 1 character.', category='error')
        elif parse(start_date) > parse(end_date):
            flash('start date can not be greater than end date.', category='error')
        elif accommodation_type not in ['Hostel', 'Hotel', 'Airbnb', 'Villa', 'Resort']:
            flash('Please enter the specified value.', category='error')
        elif int(accommodation_cost) < 0:
            flash('budget must be greater than 0.', category='error')
        elif transportation_type not in ['Train', 'Plane', 'Flight', 'Bus', 'Car rental', 'Car', 'Airplane', 'Ferry',
                                         'Subway']:
            flash('Please enter the specified value.', category='error')
        elif int(transportation_cost) < 0:
            flash('budget must be greater than 0.', category='error')
        else:
            db.histories.insert_one({
                'email': session['email'],
                'destination': destination,
                'start_date': start_date,
                'end_date': end_date,
                'accommodation_type': accommodation_type,
                'accommodation_cost': accommodation_cost,
                'transportation_type': transportation_type,
                'transportation_cost': transportation_cost,
            })
            flash('book travel successfully.', category='success')
            return redirect(url_for('views.home'))
    return render_template('/book_travel.html')
