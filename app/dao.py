from app.env import DB
from sqlalchemy import Boolean, create_engine, Column, Integer, String, Date, Float
from sqlalchemy import update
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import logging

class Base(DeclarativeBase):
    pass

class Pot(Base):
    __tablename__ = "pots"
    pot_id = Column(Integer, primary_key=True)
    cashflow_id = Column(Integer)
    name = Column(String)
    type = Column(String)
    amount = Column(Float)

    def __str__(self) -> str:
        return f"{self.pot_id} {self.cashflow_id} {self.name} {self.type} {self.amount}"

    def __repr__(self) -> str:
        return f"{self.pot_id} {self.cashflow_id} {self.name} {self.type} {self.amount}"

class Income(Base):
    __tablename__ = "incomes"
    income_id = Column(Integer, primary_key=True)
    cashflow_id = Column(Integer)
    name = Column(String)
    type = Column(String)
    amount = Column(Float)
    inflation_yearly = Column(Boolean)
    repeating_yearly = Column(Boolean)
    start_date = Column(Date)

    def __str__(self) -> str:
        return f"{self.income_id} {self.cashflow_id} {self.name} {self.type} {self.amount}"

    def __repr__(self) -> str:
        return f"{self.income_id} {self.cashflow_id} {self.name} {self.type} {self.amount}"

class Cashflow(Base):
    __tablename__ = "cashflow"
    cashflow_id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)

    def __str__(self) -> str:
        return f"{self.cashflow_id} {self.name} {self.description}"

    def __repr__(self) -> str:
        return f"{self.cashflow_id} {self.name} {self.description}"

class Parameters(Base):
    __tablename__ = "parameters"
    cashflow_id = Column(Integer, primary_key=True)
    target_income = Column(Integer)
    inflation = Column(Integer)
    growth = Column(Integer)
    age = Column(Integer)
    retirement_age = Column(Integer)
    years = Column(Integer)
    ticker = Column(String)
    historical_start_year = Column(Integer)
    charges = Column(Float)

    def __str__(self) -> str:
        return f"{self.cashflow_id} {self.target_income} {self.inflation} \
                {self.growth} {self.age} {self.retirement_age} {self.years} {self.ticker} \
                {self.historical_start_year} {self.charges}"

    def __repr__(self) -> str:
        return f"{self.cashflow_id} {self.target_income} {self.inflation} \
                {self.growth} {self.age} {self.retirement_age} {self.years} {self.ticker} \
                {self.historical_start_year} {self.charges}"

def read_pot(pot_id) -> Pot:
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    pot = session.query(Pot).get(pot_id)
    logger.info(pot)

    return pot

def update_pot(pots):
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()
    dbpots = []
    for p in pots:
           dbpots.append({"pot_id": p.pot_id,
                         "name": p.name,
                         "type": p.type,
                          "amount": p.amount})

    result = session.execute(
        update(Pot),
        dbpots,
    )
    session.commit()

def read_income(income_id) -> Income:
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    income = session.query(Income).get(income_id)

    logger.info(income)

    return income

def update_income(incomes):
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()
    dbincomes = []
    for i in incomes:
           dbincomes.append({"income_id": i.income_id,
                         "name": i.name,
                         "type": i.type,
                          "amount": i.amount,
                          "inflation_yearly": i.inflation_yearly,
                          "repeating_yearly": i.repeating_yearly,
                          "start_date": i.start_date
                             })

    result = session.execute(
        update(Income),
        dbincomes,
    )
    session.commit()

def read_parameters(cashflow_id) -> Parameters:
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()

    parameters = session.query(Parameters).get(cashflow_id)

    logger.info("Updating parameters")
    return parameters

def update_parameters(parameters):
    engine = create_engine(db.get_connection_string())
    Session = sessionmaker(bind=engine)
    session = Session()
    dbparams = []
    for p in parameters:
        dbparams.append({"cashflow_id": p.cashflow_id,
                        "target_income": p.target_income,
                         "inflation": p.inflation,
                         "growth": p.growth,
                          "age": p.age,
                          "retirement_age": p.retirement_age,
                          "years": p.years,
                          "ticker": p.ticker,
                          "historical_start_year": p.historical_start_year,
                          "charges": p.charges
                             })

    result = session.execute(
        update(Parameters),
        dbparams,
    )
    session.commit()

logger = logging.getLogger('cashflow')
db = DB()

