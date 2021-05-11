import ariadne


typedefs = ariadne.load_schema_from_path('./schema/')

schema = ariadne.make_executable_schema(typedefs)
