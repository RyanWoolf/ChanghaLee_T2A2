from config import db


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(), nullable=False)