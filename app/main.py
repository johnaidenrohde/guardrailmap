from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import create_access_token, decode_access_token, hash_password, verify_password
from .database import Base, engine, get_db
from .models import Comment, GuardrailFeature, Photo, User
from .schemas import CommentCreate, CommentOut, FeatureCreate, FeatureOut, LoginRequest, Token, UserCreate, UserOut
from .storage import upload_photo

Base.metadata.create_all(bind=engine)

app = FastAPI(title='GuardrailMap API')
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

static_dir = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=static_dir), name='static')


@app.get('/')
def root() -> FileResponse:
    return FileResponse(static_dir / 'index.html')


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing bearer token')
    token = authorization.split(' ', 1)[1]
    username = decode_access_token(token)
    if not username:
        raise HTTPException(status_code=401, detail='Invalid token')

    user = db.scalar(select(User).where(User.username == username))
    if not user:
        raise HTTPException(status_code=401, detail='User not found')
    return user


@app.post('/api/register', response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=400, detail='Username already exists')
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=400, detail='Email already exists')

    user = User(username=payload.username, email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post('/api/login', response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    return Token(access_token=create_access_token(user.username))


@app.get('/api/features', response_model=list[FeatureOut])
def list_features(db: Session = Depends(get_db)):
    return db.scalars(select(GuardrailFeature).order_by(GuardrailFeature.id.desc())).all()


@app.post('/api/features', response_model=FeatureOut)
def create_feature(payload: FeatureCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _ = user
    feature = GuardrailFeature(**payload.model_dump())
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return feature


@app.post('/api/features/{feature_id}/comments', response_model=CommentOut)
def add_comment(feature_id: int, payload: CommentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    feature = db.get(GuardrailFeature, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail='Feature not found')
    comment = Comment(feature_id=feature_id, user_id=user.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.post('/api/features/{feature_id}/photos')
def add_photo(feature_id: int, file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    feature = db.get(GuardrailFeature, feature_id)
    if not feature:
        raise HTTPException(status_code=404, detail='Feature not found')

    file_bytes = file.file.read()
    object_key, image_url = upload_photo(file_bytes, file.content_type or 'image/jpeg', file.filename or 'upload.jpg')

    photo = Photo(feature_id=feature_id, user_id=user.id, object_key=object_key, image_url=image_url)
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return {'photo_id': photo.id, 'image_url': photo.image_url}
