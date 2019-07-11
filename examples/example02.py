import upref
data = upref.get_pref(
    {
        'login': {'label': "Your login"},
        'passwd': {'label': "Your secret password",
                   'type': "Password"},
    },
    name="example02")
print("Your login is %s" % data['login'])
print("Your password (not so secret) is %s" % data['passwd'])
