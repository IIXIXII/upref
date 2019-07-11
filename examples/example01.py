import upref

user_data = upref.get_pref(
    {"url": {"label": "The application url"}},
    "example01")

print("URL is {}".format(user_data['url']))
