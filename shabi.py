dict1 = {'email': 'shabi.@gmail'}
result = dict1.get('email', None)

# print(type(result))

if result:
    print('this key exist')
else:
    print('this key doesnot exist')
