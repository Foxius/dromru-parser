import os
homeDir = (r'\\').join(os.path.abspath(__file__).split('\\')[:-1])


db_path = f'{homeDir}\\DB\\db.db'

