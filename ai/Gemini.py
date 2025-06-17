from google import genai
from google.genai import types
import json

# migrated to from google.generativeai to google-genai
# https://github.com/googleapis/python-genai

class GeminiClient:
    '''
    GeminiClient
      running gemini-2.0-flash
     ∷ _parse
     ∷ generateSongs
        ↳ model.generate_content
        returns: _parse(content)
    '''
    def __init__(self, apiKey):
        self.apiKey = apiKey
        self.client = genai.Client(api_key=self.apiKey,http_options=types.HttpOptions(api_version='v1beta'))
        self.model = 'gemini-2.5-flash-preview-05-20'

    def _parse(self, text):
        cleaned = text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[len('```json'):]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-len('```')]
        
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            if cleaned.strip().endswith(',]'):
                cleaned = cleaned.strip()[:-2] + ']'
                try:
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    pass 
            raise e

    def generateSongs(self, description, length, seedSongs):
        seedList = ''
        for metadata in seedSongs:
            seedList += f'{metadata['song']} by {metadata['artist']}, '

        prompt = f"""
        Create a list of {length} songs.
        Follow the description: {description}
        Take the following songs into consideration as examples of style of genre:
        {seedList}
        Provide the output as a valid JSON array of objects, where each object has a "song" key and an "artist" key.
        Example: [{{"song": "Bohemian Rhapsody", "artist": "Queen"}}, {{"song": "Stairway to Heaven", "artist": "Led Zeppelin"}}]
        """
        response = self.client.models.generate_content(
            model=self.model, contents=prompt
        )
        return self._parse(response.text)