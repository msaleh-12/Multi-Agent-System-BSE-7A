"""
Search Node - Finds educational resources (articles & videos) in parallel
"""

import logging
import os
import asyncio
from typing import Dict, Any, List

_logger = logging.getLogger(__name__)

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"


async def search_resources(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for articles and videos in parallel based on keywords.
    
    Args:
        state: Current workflow state with 'keywords' and 'preferences'
        
    Returns:
        Updated state with 'articles' and 'videos' fields
    """
    _logger.info("🔎 Starting resource search...")
    
    try:
        keywords = state.get("keywords", [])
        preferences = state.get("preferences", {})
        
        if not keywords:
            _logger.warning("⚠️ No keywords available, skipping search")
            state["articles"] = []
            state["videos"] = []
            return state
        
        # Search articles and videos in parallel
        articles_task = _search_articles(keywords, preferences)
        videos_task = _search_videos(keywords, preferences)
        
        articles, videos = await asyncio.gather(articles_task, videos_task)
        
        state["articles"] = articles
        state["videos"] = videos
        
        _logger.info(f"✅ Search complete: {len(articles)} articles, {len(videos)} videos")
        return state
        
    except Exception as e:
        _logger.error(f"❌ Resource search failed: {e}")
        state["error"] = f"Search error: {str(e)}"
        state["articles"] = []
        state["videos"] = []
        return state


async def _search_articles(keywords: List[str], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search for educational articles."""
    if not preferences.get("include_articles", True):
        return []
    
    # Get more candidates than needed for better aggregation
    # Aggregation will handle final limiting and ranking
    limit = preferences.get("resource_limit", 10) * 2
    
    if USE_MOCK:
        return await _mock_search_articles(keywords, limit)
    else:
        return await _real_search_articles(keywords, limit)


async def _search_videos(keywords: List[str], preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Search for educational videos."""
    if not preferences.get("include_videos", True):
        return []
    
    # Get more candidates than needed for better aggregation
    # Aggregation will handle final limiting and ranking
    limit = preferences.get("resource_limit", 10) * 2
    
    if USE_MOCK:
        return await _mock_search_videos(keywords, limit)
    else:
        return await _real_search_videos(keywords, limit)


async def _mock_search_articles(keywords: List[str], limit: int) -> List[Dict[str, Any]]:
    """Mock article search for testing."""
    _logger.info("🎭 Using MOCK article search")
    
    # Generate contextual articles based on keywords
    topic = keywords[0] if keywords else "programming"
    
    articles = [
        {
            "title": f"Introduction to {topic.title()}: A Comprehensive Guide",
            "url": f"https://example.com/articles/{topic.replace(' ', '-')}-guide",
            "description": f"Learn the fundamentals of {topic} with this detailed tutorial covering core concepts and practical examples.",
            "source": "web_search",
            "relevance_score": 0.95
        },
        {
            "title": f"Advanced {topic.title()} Techniques and Best Practices",
            "url": f"https://example.com/articles/advanced-{topic.replace(' ', '-')}",
            "description": f"Master advanced techniques in {topic} and learn industry best practices from experts.",
            "source": "web_search",
            "relevance_score": 0.88
        },
        {
            "title": f"{topic.title()} Tutorial for Beginners",
            "url": f"https://example.com/tutorials/{topic.replace(' ', '-')}-beginners",
            "description": f"Step-by-step tutorial for beginners learning {topic}. No prior experience required.",
            "source": "web_search",
            "relevance_score": 0.82
        },
        {
            "title": f"Common Mistakes in {topic.title()} and How to Avoid Them",
            "url": f"https://example.com/articles/{topic.replace(' ', '-')}-mistakes",
            "description": f"Learn from common pitfalls and mistakes beginners make when learning {topic}.",
            "source": "web_search",
            "relevance_score": 0.78
        },
        {
            "title": f"The Complete {topic.title()} Handbook",
            "url": f"https://example.com/handbook/{topic.replace(' ', '-')}",
            "description": f"Comprehensive reference guide covering everything you need to know about {topic}.",
            "source": "web_search",
            "relevance_score": 0.75
        }
    ]
    
    return articles[:limit]


async def _mock_search_videos(keywords: List[str], limit: int) -> List[Dict[str, Any]]:
    """Mock video search for testing."""
    _logger.info("🎭 Using MOCK video search")
    
    topic = keywords[0] if keywords else "programming"
    
    videos = [
        {
            "title": f"{topic.title()} Explained in 10 Minutes",
            "url": f"https://youtube.com/watch?v=mock_{topic.replace(' ', '_')}_1",
            "thumbnail": f"https://img.youtube.com/vi/mock_{topic}/maxresdefault.jpg",
            "channel": "Educational Tech",
            "duration": "10:23",
            "source": "video_platform",
            "relevance_score": 0.92
        },
        {
            "title": f"Complete {topic.title()} Course - Full Tutorial",
            "url": f"https://youtube.com/watch?v=mock_{topic.replace(' ', '_')}_2",
            "thumbnail": f"https://img.youtube.com/vi/mock_{topic}/hqdefault.jpg",
            "channel": "CodeAcademy",
            "duration": "2:45:30",
            "source": "video_platform",
            "relevance_score": 0.89
        },
        {
            "title": f"{topic.title()} Crash Course for Beginners",
            "url": f"https://youtube.com/watch?v=mock_{topic.replace(' ', '_')}_3",
            "thumbnail": f"https://img.youtube.com/vi/mock_{topic}/hqdefault.jpg",
            "channel": "Programming with Tech",
            "duration": "45:12",
            "source": "video_platform",
            "relevance_score": 0.85
        },
        {
            "title": f"Advanced {topic.title()} Masterclass",
            "url": f"https://youtube.com/watch?v=mock_{topic.replace(' ', '_')}_4",
            "thumbnail": f"https://img.youtube.com/vi/mock_{topic}/hqdefault.jpg",
            "channel": "Tech Masters",
            "duration": "1:30:00",
            "source": "video_platform",
            "relevance_score": 0.80
        },
        {
            "title": f"{topic.title()} Project Tutorial - Build Real Applications",
            "url": f"https://youtube.com/watch?v=mock_{topic.replace(' ', '_')}_5",
            "thumbnail": f"https://img.youtube.com/vi/mock_{topic}/hqdefault.jpg",
            "channel": "Project Based Learning",
            "duration": "3:15:45",
            "source": "video_platform",
            "relevance_score": 0.77
        }
    ]
    
    return videos[:limit]


async def _real_search_articles(keywords: List[str], limit: int) -> List[Dict[str, Any]]:
    """Real article search using Tavily API."""
    try:
        from tavily import TavilyClient
        
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set. Use USE_MOCK=true for testing.")
        
        _logger.info("🌐 Using Tavily for article search")
        
        client = TavilyClient(api_key=api_key)
        query = " ".join(keywords[:3])  # Use top 3 keywords
        
        response = client.search(
            query=f"{query} tutorial education",
            max_results=limit,
            search_depth="advanced"
        )
        
        articles = []
        for result in response.get("results", []):
            articles.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "description": result.get("content", ""),
                "source": "web_search",
                "relevance_score": result.get("score", 0.5)
            })
        
        return articles
        
    except ImportError:
        _logger.error("Tavily SDK not installed")
        raise
    except Exception as e:
        _logger.error(f"Tavily search failed: {e}")
        raise


async def _real_search_videos(keywords: List[str], limit: int) -> List[Dict[str, Any]]:
    """Real video search using YouTube Data API v3."""
    try:
        from googleapiclient.discovery import build
        
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY not set. Use USE_MOCK=true for testing.")
        
        _logger.info("📺 Using YouTube API for video search")
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        query = " ".join(keywords[:3])
        
        search_response = youtube.search().list(
            q=f"{query} tutorial education",
            part='id,snippet',
            maxResults=limit,
            type='video',
            videoCategoryId='27',  # Education category
            relevanceLanguage='en'
        ).execute()
        
        videos = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            snippet = item['snippet']
            
            # Get video duration (requires additional API call)
            video_details = youtube.videos().list(
                part='contentDetails',
                id=video_id
            ).execute()
            
            duration = video_details['items'][0]['contentDetails']['duration'] if video_details['items'] else "Unknown"
            
            videos.append({
                "title": snippet['title'],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": snippet['thumbnails']['high']['url'],
                "channel": snippet['channelTitle'],
                "duration": duration,
                "source": "video_platform",
                "relevance_score": 0.85  # YouTube doesn't provide scores
            })
        
        return videos
        
    except ImportError:
        _logger.error("Google API client not installed")
        raise
    except Exception as e:
        _logger.error(f"YouTube API search failed: {e}")
        raise
