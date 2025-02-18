#%%
attributes = dict(foo="Bar", prot = 5)


formatted_attributes = {
    key: str(value)
    for key, value in attributes.items()
}
formatted_attributes
# %%
