from sqlalchemy import create_engine, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    username: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(String(30))
    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, username={self.username!r}, password={self.password!r})"

class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(30))
    subject: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(1000))
    def __repr__(self) -> str:
        return f"Question(id={self.id!r}, owner={self.owner!r}, subject={self.subject!r}, title={self.title!r}, description={self.description!r})"

engine = create_engine("sqlite:///users.db", echo=False)