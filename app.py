import os
from functools import partial
from re import search

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

app = Flask(__name__)
cache.init_app(app)

base = os.path.abspath(os.path.join(__file__, ".."))

page_number_cache = {}


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@cache.memoize(timeout=60)
def slug_exists(slug: str):
    return os.path.exists(os.path.join(base, "media", slug))


@cache.memoize(timeout=60)
def chapter_exists(slug: str, chapter_name: str):
    return os.path.exists(os.path.join(base, "media", slug, chapter_name))


@cache.memoize(timeout=60)
def get_chapters(slug: str):
    chapter_names = [item for item in os.listdir(os.path.join(base, "media", slug)) if
                     not item.startswith(".") and os.path.isdir(os.path.join(base, "media", slug, item))]
    chapter_names.sort(key=lambda item: float(item) if " - " not in item else float(item.partition(" - ")[0]))
    return chapter_names


@app.route('/')
@cache.cached(timeout=60)
def home():
    names = [item for item in os.listdir(os.path.join(base, "media")) if
             not item.startswith(".") and os.path.isdir(os.path.join(base, "media", item))]
    names.sort()
    return render_template("homepage.html", names=names, count=len(names))


@app.route("/<slug>")
@cache.memoize(timeout=60)
def chapters(slug: str):
    if not slug_exists(slug):
        abort(404)
    else:
        chapter_names = get_chapters(slug)
        return render_template("manga.html", chapter_names=chapter_names, count=len(chapter_names) + 1, name=slug.replace("-", " "), slug=slug)


@app.route("/<slug>/<chapter>")
@cache.memoize(timeout=60)
def pages(slug: str, chapter: str):
    chapter = chapter.replace("_", " ")
    if not chapter_exists(slug, chapter):
        return abort(404)
    else:
        page_names = [(int(item.partition(".")[0]), item) for item in os.listdir(os.path.join(base, "media", slug, chapter)) if
                      not item.startswith(".") and os.path.isfile(os.path.join(base, "media", slug, chapter, item))]
        page_names.sort(key=lambda item: item[0])
        return render_template("chapter.html", pages=page_names, count=len(page_names), manga_name=slug.replace("-", " "), slug=slug, name=chapter)


@app.route("/<slug>/<chapter>/<page>")
def individual_page(slug: str, chapter: str, page: str):
    return send_from_directory(os.path.join(base, "media", slug, chapter.replace("_", " ")), page)


def sort_chapter_page(item: str, slug: str):
    non_ext = item.rpartition(".")[0]
    chapter, page = non_ext.split("/")
    slug_data = page_number_cache.setdefault(slug, {})
    data = slug_data.setdefault("data", {})
    count = slug_data.setdefault("count", -1)
    if match := search(r"^([\d.]+)", chapter):
        return float(match.group(1)), int(page)
    else:
        slug_data["count"] -= 1
        return data.setdefault(chapter, count), int(page)


@app.route("/<slug>/combined")
@cache.memoize(timeout=60)
def combined(slug: str):
    if not slug_exists(slug):
        abort(404)
    page_names_basic = []
    for current_dir, folders, files in os.walk(os.path.join(base, "media", slug)):
        if current_dir == os.path.join(base, "media", slug) or current_dir.startswith("."):
            continue
        for file in files:
            if not file.startswith(".") and os.path.isfile(os.path.join(current_dir, file)):
                page_names_basic.append(f"{os.path.basename(current_dir).replace(' ', '_')}/{file}")
    page_names_basic.sort(key=partial(sort_chapter_page, slug=slug))
    page_names = [(num, item) for num, item in enumerate(page_names_basic, start=1)]
    return render_template("chapter.html", pages=page_names, count=len(page_names), manga_name=slug.replace("-", " "), slug=slug, name="Combined",
                           combined=True)


@app.route("/previous/<slug>/<chapter>")
def go_prev(slug: str, chapter: str):
    chapters = get_chapters(slug)
    official = chapter.replace("_", " ")
    if official not in chapters:
        return abort(404)
    index = chapters.index(official)
    if index == 0:
        return redirect(f"/{slug}")
    else:
        return redirect(f"/{slug}/{chapters[index - 1].replace(' ', '_')}")


@app.route("/next/<slug>/<chapter>")
def go_next(slug: str, chapter: str):
    chapters = get_chapters(slug)
    official = chapter.replace("_", " ")
    if official not in chapters:
        return abort(404)
    index = chapters.index(official)
    if index == len(chapters) - 1:
        return redirect(f"/{slug}")
    else:
        return redirect(f"/{slug}/{chapters[index + 1].replace(' ', '_')}")


@app.route("/stop")
def stop():
    if request.remote_addr in ["127.0.0.1"] or search(r"192\.168\.(\d{1,3})\.(\d{1,3})", request.remote_addr) \
            or request.headers.get("X-Forwarded-For", "127.0.0.1") in ["127.0.0.1"] \
            or search(r"192\.168\.(\d{1,3})\.(\d{1,3})", request.headers.get("X-Forwarded-For", "127.0.0.1")):  # Local address or my IP
        shutdown_server()
        return "", 204
    else:
        return abort(403)


@app.route("/api")
@cache.memoize(timeout=60)
def api():
    names = [item for item in os.listdir(os.path.join(base, "media")) if
             not item.startswith(".") and os.path.isdir(os.path.join(base, "media", item))]
    names.sort()
    return jsonify(names)


@app.route("/api/<slug>")
@cache.memoize(timeout=60)
def api_slug(slug: str):
    if not slug_exists(slug):
        abort(404)
    else:
        chapter_names = get_chapters(slug)
        return jsonify(chapter_names)


@app.route("/api/<slug>/<chapter>")
@cache.memoize(timeout=60)
def api_chapter(slug: str, chapter: str):
    chapter = chapter.replace("_", " ")
    if not chapter_exists(slug, chapter):
        return abort(404)
    else:
        page_names = [(int(item.partition(".")[0]), item) for item in os.listdir(os.path.join(base, "media", slug, chapter)) if
                      not item.startswith(".") and os.path.isfile(os.path.join(base, "media", slug, chapter, item))]
        page_names.sort(key=lambda item: item[0])
        return jsonify(list(item[1] for item in page_names))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=False)
