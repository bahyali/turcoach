from fastapi import FastAPI

from models import Pitch

app = FastAPI()


@app.get("/pitch/list/to_be_maintained")
def read_should_maintain():
    results = Pitch.find(
        Pitch.condition_score < 10,
        Pitch.condition_score >= 2,
        Pitch.can_be_maintained == True,
    )

    if results.count() > 0:
        return results.to_list()
    else:
        return []


@app.get("/pitch/list/to_be_replaced")
def read_should_replace():
    return Pitch.find(Pitch.condition_score <= 2).to_list()


@app.get("/pitch/all")
def list_pitches():
    return Pitch.all().to_list()


@app.post("/pitch")
def create_pitch(pitch: Pitch):
    return pitch.insert()
