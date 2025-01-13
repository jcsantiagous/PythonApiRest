from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from typing import Optional
from models import UserModel

def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    """
    Obtiene un usuario por su email
    :rtype: object
    """
    try:
        return db.query(UserModel).filter(UserModel.email == email).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar la base de datos: {str(e)}"
        )

def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    """
    Obtiene un usuario por su nombre de usuario
    """
    try:
        return db.query(UserModel).filter(UserModel.username == username).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al consultar la base de datos: {str(e)}"
        )

def create_user(db: Session, user_data: dict) -> UserModel:
    """
    Crea un nuevo usuario
    """
    try:
        db_user = UserModel(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el usuario: {str(e)}"
        )