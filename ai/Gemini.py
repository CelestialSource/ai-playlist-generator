import google.generativeai as genai
import json

class GeminiClient:
    def __init__(self, apiKey):
        self.apiKey = apiKey
        genai.configure(apiKey=self.apiKey)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

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

    def generateSongs(self, length, seedSongs):
        seedList = ''
        for uri in seedSongs:
            seedList += f'{seedSongs[uri].song} by {seedSongs[uri].artist}, '

        prompt = f"""
        Create a list of {length} songs.
        Take the following songs into consideration as examples of style of genre:
        {seedList}
        Provide the output as a valid JSON array of objects, where each object has a "song" key and an "artist" key.
        Example: [{{"song": "Bohemian Rhapsody", "artist": "Queen"}}, {{"song": "Stairway to Heaven", "artist": "Led Zeppelin"}}]
        """
        response = self.model.generate_content(prompt)
        return self._parse(response.text)