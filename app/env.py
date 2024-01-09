import os

class DB:
    def __init__(self):
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_name = os.getenv('DB_NAME')

        # dialect+driver://username:password@host:port/database
        self.connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    def get_connection_string(self):
        return self.connection_string

class ENV:
    def __init__(self):
        cashflow_tabs = os.getenv("CASHFLOW_TABS")
        if cashflow_tabs:
            self.cashflow_tabs = cashflow_tabs.split(",")
        else:
            self.cashflow_tabs = ['p1','p2']

        cashflow_incomes = os.getenv("CASHFLOW_INCOMES")
        if cashflow_incomes:
            self.cashflow_incomes = cashflow_incomes.split(",")
        else:
            self.cashflow_incomes = ['i1','i2','i3','i4']


