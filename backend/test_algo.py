from db.database import engine
from models.domain import Base
from sqlalchemy.orm import Session
from services.smoothing_algorithm import process_income_event

Base.metadata.create_all(bind=engine)
with Session(engine) as db:
    try:
        print("FIRST INCOME 800")
        print(process_income_event(db, 1, 800))
        print("SECOND INCOME 150")
        print(process_income_event(db, 1, 150))
    except Exception as e:
        import traceback
        traceback.print_exc()
