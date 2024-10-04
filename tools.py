from urllib.parse import urlparse
from langchain_community.document_loaders import WebBaseLoader

from open_ai import ai_summarize_page_content
from langchain_community.document_loaders import YoutubeLoader

language_codes = [
    "en", "ru", "uk", "de", "es", "ab", "aa", "af", "ak", "sq", "am", "ar", "hy", "as", "ay", "az", "bn", "ba", "eu", "be", "bho", "bs", "br", "bg", "my",
    "ca", "ceb", "zh-Hans", "zh-Hant", "co", "hr", "cs", "da", "dv", "nl", "dz", "en", "eo", "et", "ee", "fo", "fj", "fil",
    "fi", "fr", "gaa", "gl", "lg", "ka", "de", "el", "gn", "gu", "ht", "ha", "haw", "iw", "hi", "hmn", "hu", "is", "ig", "id",
    "ga", "it", "ja", "jv", "kl", "kn", "kk", "kha", "km", "rw", "ko", "kri", "ku", "ky", "lo", "la", "lv", "ln", "lt", "luo",
    "lb", "mk", "mg", "ms", "ml", "mt", "gv", "mi", "mr", "mn", "mfe", "ne", "new", "nso", "no", "ny", "oc", "or", "om", "os",
    "pam", "ps", "fa", "pl", "pt", "pt-PT", "pa", "qu", "ro", "rn", "ru", "sm", "sg", "sa", "gd", "sr", "crs", "sn", "sd", "si",
    "sk", "sl", "so", "st", "es", "su", "sw", "ss", "sv", "tg", "ta", "tt", "te", "th", "bo", "ti", "to", "ts", "tn", "tum",
    "tr", "tk", "uk", "ur", "ug", "uz", "ve", "vi", "war", "cy", "fy", "wo", "xh", "yi", "yo", "zu"
]

async def process_urls(message: str):
    # Split the string into words
    words = message.split()

    # Extract URLs from the words using urlparse()
    urls = []
    for word in words:
        parsed = urlparse(word)
        if parsed.scheme and parsed.netloc:
            urls.append(word)

    if len(urls) == 0:
        return None

    url = str(urls[0])

    if url.find("t.me") != -1:
        return None

    loader = None
    if url.find("youtube") != -1 or url.find("youtu.be") != -1:
        loader = YoutubeLoader.from_youtube_url(url, add_video_info=True, language=language_codes)
    else:
        loader = WebBaseLoader(web_paths=[urls[0]])

    docs = []
    async for doc in loader.alazy_load():
        docs.append(doc)

    summaries = []
    for doc in docs:
        doc.page_content = ai_summarize_page_content(doc.page_content)
        summaries.append(doc)

    return summaries
