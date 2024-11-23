import asyncio
from typing import List, Optional
from urllib.parse import urlparse
from langchain_community.document_loaders import WebBaseLoader

from open_ai import ai_summarize_page_content
from langchain_community.document_loaders import YoutubeLoader
from pytube.exceptions import PytubeError

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

non_supported_urls = [
    "t.me",
    "youtube.com",
    "youtu.be",
    "maps.",
    "reddit.com",
    "tiktok.com",
    "x.com",
    "instagram.com",
    "egov.uscis.gov",
]
async def process_urls(message: str) -> Optional[List]:
    """
    Process URLs found in the input message.

    Extracts the first valid URL from the message, creates an appropriate loader
    based on the URL type (YouTube or web), and loads the document with retry logic
    for YouTube videos. Summarizes the page content using AI.

    Args:
        message (str): The input message containing URLs.

    Returns:
        Optional[List]: A list containing the processed document or None if processing fails.
    """
    urls = extract_urls_from_message(message)
    if not urls:
        return None

    url = urls[0]

    if any(non_supported_url in url for non_supported_url in non_supported_urls):
        return None

    loader = create_loader_for_url(url)
    if not loader:
        return None

    document = await load_document_with_retries(loader)
    if not document:
        print("Failed to load the document after maximum retries.")
        return None

    document.page_content = ai_summarize_page_content(document.page_content)
    return [document]


def extract_urls_from_message(message: str) -> List[str]:
    """
    Extracts URLs from the input message.

    Args:
        message (str): The input message containing potential URLs.

    Returns:
        List[str]: A list of extracted URLs.
    """
    words = message.split()
    urls = []
    for word in words:
        parsed_url = urlparse(word)
        if parsed_url.scheme and parsed_url.netloc:
            urls.append(word)
    return urls


def create_loader_for_url(url: str):
    """
    Creates an appropriate loader based on the URL.

    Args:
        url (str): The URL to create a loader for.

    Returns:
        Loader object or None if URL is unsupported.
    """
    if "youtube" in url or "youtu.be" in url:
        return YoutubeLoader.from_youtube_url(
            url, add_video_info=True, language=language_codes
        )
    elif "http" in url or "https" in url:
        return WebBaseLoader(web_paths=[url])
    else:
        print("Unsupported URL format.")
        return None


async def load_document_with_retries(loader, max_retries: int = 20):
    """
    Loads a document using the provided loader with retry logic for PytubeError.

    Args:
        loader: The document loader instance.
        max_retries (int): Maximum number of retry attempts.

    Returns:
        The loaded document or None if all retries fail.
    """
    for attempt in range(1, max_retries + 1):
        try:
            documents = loader.load()
            if documents:
                return documents[0]
            else:
                print("No documents were returned by the loader.")
                return None
        except PytubeError:
            print(f"Failed to load the video. Retrying... ({attempt}/{max_retries})")
            await asyncio.sleep(2)  # Optional delay between retries
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise
    return None
