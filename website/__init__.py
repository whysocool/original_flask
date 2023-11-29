from flask import Flask
import pymongo
import pandas as pd

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient["mydatabase"]
CSV_PATH = "./Travel details dataset.csv"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dfkdfdkl'  # mandatory. because we need to use session

    from . import views, auth

    app.register_blueprint(views.bp)
    app.register_blueprint(auth.bp)
    create_2_collections(CSV_PATH, db)

    return app


def create_2_collections(path_of_csv, db):
    # in implementation process, we may run the code many times,so we need to make sure not to insert csv file twice
    list_of_collections = db.list_collection_names()
    if not ('histories' in list_of_collections):  # the first time we run our code
        # load csv file
        # data preprocess. After preprocessing, only 136 entries are available
        df = pd.read_csv(path_of_csv).dropna(axis=0, how='any')  # # drop nan. 136 valid rows
        df = df.reset_index(drop=True)

        # convert nation to nationality in nationality column
        def clean_nationality(df, column_name):
            nation_list = ['Italy', 'China', 'Canada', 'South Korea', 'USA', 'Spain', 'Japan', 'Brazil', 'Germany',
                           'United Kingdom', 'Hong Kong', 'Singapore', 'Greece', 'Cambodia']
            nationality_list = ['Italian', 'Chinese', 'Canadian', 'South Korean', 'American', 'Spanish', 'Japanese',
                                'Brazilian',
                                'German',
                                'UK', 'Hong Kongese', 'Singaporean', 'Greek', 'Cambodian']
            column_nationality = df[column_name].copy()
            for i in range(len(column_nationality)):
                if column_nationality[i] in nation_list:
                    column_nationality[i] = nationality_list[nation_list.index(column_nationality[i])]
            return column_nationality

        df['Traveler nationality'] = clean_nationality(df, 'Traveler nationality')

        # clear string or symbol in column 'Accommodation cost' and 'Transportation cost'
        def extract_digit_for_column(df, column_name):
            column_new = df[column_name].copy()
            for i in range(len(column_new)):
                string_now = column_new[i]
                num = ""
                for c in string_now:
                    if c.isdigit():
                        num = num + c
                column_new[i] = num
            return column_new

        df['Accommodation cost'] = extract_digit_for_column(df, 'Accommodation cost')
        df['Transportation cost'] = extract_digit_for_column(df, 'Transportation cost')

        # remove country from destination
        def remove_country_from_destination(df, column_name):
            column_new = df[column_name].copy()
            for i in range(len(column_new)):
                column_new[i] = column_new[i].split(', ')[0]
            return column_new

        df['Destination'] = remove_country_from_destination(df, 'Destination')

        # change New York City to New York
        def remove_duplicate_destination(df, column_name):
            # New York City -> New York
            column_Destination = df[column_name].copy()
            for i in range(len(column_Destination)):
                if column_Destination[i] == 'New York City':
                    column_Destination[i] = 'New York'
            return column_Destination

        df['Destination'] = remove_duplicate_destination(df, 'Destination')

        # add documents for 2 collections
        # since the dataset provided is not complete we need to add email for each user in the histories collection to help us connect 2 collections
        # let's use index as email for each user
        for index, row in df.iterrows():
            new_user = {
                'fullName': row['Traveler name'],
                'email': str(index) + '@gmail.com',  # email must be distinct
                'nationality': row['Traveler nationality'],
                'age': row['Traveler age'],
                'gender': row['Traveler gender'],
                'budget_accommodation': row['Accommodation cost'],
                'budget_transportation': row['Transportation cost'],
            }
            db.users.insert_one(new_user)
            new_history = {
                'email': str(index) + '@gmail.com',
                'destination': row['Destination'],
                'start_date': row['Start date'],
                'end_date': row['End date'],
                'accommodation_type': row['Accommodation type'],
                'accommodation_cost': row['Accommodation cost'],
                'transportation_type': row['Transportation type'],
                'transportation_cost': row['Transportation cost'],
            }
            db.histories.insert_one(new_history)
        print('-----------------------------------')
        print('writing csv into mongodb completed.')
        print('-----------------------------------')
    return
