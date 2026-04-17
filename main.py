import re
import requests
import threading
from urllib.parse import urlparse, parse_qs

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window


API_KEY = "AIzaSyApJUd6i-9wsRXGj-_-67peidGmd1QD3A"

KEYWORDS = [
    "Abucay","Anislag","Bacacay","Bacong","Baligang","Basag","Basicao","Guinobatan",
    "Bayasong","Buga","Cabraran","Caburacan","Camalig","Carisac","Castilla",
    "Catburawan","Claveria","Dancalan","Daraga","Diaro","Dinapa","Donsol",
    "Duhang Puro","Esperanza","Batan","Inapugan","Labnig","Langaton",
    "Legazpi City","Libon","Ligao City","Lobos","Lomacao","Mabuhay","Malbog",
    "Malilipot","Malinao","Mamlad","Manito","Mariroc","Masarawag","Napo",
    "Palanog","Pasig","Paulba","Pilar","Pinamandayan","Pio Duran","Poblacion 2",
    "Polangui","Queromero","Recodo","Rizal","San Antonio","San Isidro","San Jose",
    "San Pascual","San Pedro","San Rafael","San Ramon","San Vicente","Sevilla",
    "Sinungtan","Sta Misericordia","Tabaco City","Tambac","Taysan","Tiwi"
]

KEYWORDS_LC = {k.lower(): k for k in KEYWORDS}


# ---------------- FILE SAVE ----------------
def get_storage_path():
    import os
    try:
        from kivy.app import App
        return App.get_running_app().user_data_dir
    except:
        return "."


def load_last_url():
    try:
        with open(get_storage_path() + "/last_url.txt", "r") as f:
            return f.read().strip()
    except:
        return ""


def save_last_url(url):
    with open(get_storage_path() + "/last_url.txt", "w") as f:
        f.write(url)


# ---------------- VIDEO ID ----------------
def extract_video_id(url):
    parsed = urlparse(url)

    if parsed.hostname == "youtu.be":
        return parsed.path[1:]

    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        return parse_qs(parsed.query).get("v", [None])[0]

    return None


def normalize_text(text):
    return re.sub(r'<.*?>', '', text).lower()


# ---------------- CORE LOGIC ----------------
def locality_comment_counter(video_id, callback):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"

    next_page_token = None
    results = {k: 0 for k in KEYWORDS}
    total = 0
    page = 0

    session = requests.Session()

    while True:
        page += 1

        params = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": 100,
            "key": API_KEY,
            "pageToken": next_page_token,
            "textFormat": "plainText"
        }

        response = session.get(url, params=params)
        data = response.json()

        if "items" not in data:
            break

        for item in data["items"]:
            comments = [item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]]

            if "replies" in item:
                comments.extend(
                    r["snippet"]["textDisplay"] for r in item["replies"]["comments"]
                )

            for c in comments:
                norm = normalize_text(c)

                for k, original in KEYWORDS_LC.items():
                    if k in norm:
                        results[original] += 1
                        total += 1
                        break

        next_page_token = data.get("nextPageToken")

        callback(page, results, total)

        if not next_page_token:
            break


# ---------------- UI ----------------
class RootUI(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.padding = 10
        self.spacing = 10

        self.add_widget(Label(text="📊 Locality Comment Analyzer", font_size=20))

        self.url_input = TextInput(
            hint_text="Paste YouTube URL here",
            text=load_last_url(),
            multiline=False,
            size_hint_y=None,
            height=50
        )
        self.add_widget(self.url_input)

        self.btn = Button(text="Analyze", size_hint_y=None, height=50)
        self.btn.bind(on_press=self.start)
        self.add_widget(self.btn)

        self.progress = ProgressBar(max=100)
        self.add_widget(self.progress)

        self.status = Label(text="Ready")
        self.add_widget(self.status)

        self.output = Label(text="", size_hint_y=None)
        self.output.bind(texture_size=self.output.setter('size'))

        scroll = ScrollView()
        scroll.add_widget(self.output)
        self.add_widget(scroll)

    def start(self, instance):
        url = self.url_input.text.strip()

        if not url:
            self.output.text = "❌ No URL"
            return

        save_last_url(url)

        video_id = extract_video_id(url)

        if not video_id:
            self.output.text = "❌ Invalid URL"
            return

        self.btn.disabled = True
        self.status.text = "Running..."
        self.progress.value = 0

        thread = threading.Thread(
            target=self.run_analysis,
            args=(video_id,)
        )
        thread.start()

    def run_analysis(self, video_id):
        def update(page, results, total):
            self.progress.value = min(page * 10, 90)

            sorted_data = sorted(results.items(), key=lambda x: x[1], reverse=True)

            text = "📍 RESULTS\n\n"
            top = None
            rank = 1

            for k, v in sorted_data:
                if v > 0:
                    if not top:
                        top = k
                    text += f"{rank}. {k} — {v}\n"
                    rank += 1

            text += f"\nTotal: {total}"
            text += f"\nTop: {top if top else 'None'}"

            self.output.text = text

        locality_comment_counter(video_id, update)

        self.status.text = "Done ✔"
        self.btn.disabled = False
        self.progress.value = 100


class LocalityApp(App):
    def build(self):
        return RootUI()


if __name__ == "__main__":
    LocalityApp().run()
