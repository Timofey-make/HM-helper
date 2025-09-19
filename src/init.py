from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(String(30))
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.username!r}, password={self.password!r})"

engine = create_engine("sqlite:///users.db", echo=False)