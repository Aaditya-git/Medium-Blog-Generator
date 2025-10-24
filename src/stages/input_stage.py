from dataclasses import dataclass
from ..utils.slugify import slugify
from ..utils.timestamps import today_slug, timestamp_iso

@dataclass
class InputContext:
    topic: str
    tone: str
    topic_slug: str
    date_slug: str
    started_at: str

def run(topic: str, tone: str | None) -> InputContext:
    return InputContext(
        topic=topic,
        tone=tone or 'concise, friendly, practical',
        topic_slug=slugify(topic),
        date_slug=today_slug(),
        started_at=timestamp_iso()
    )
