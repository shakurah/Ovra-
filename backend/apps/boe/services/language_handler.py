"""
Language detection and translation handler for multi-language support
"""

from typing import Tuple, Optional
import langid
from googletrans import Translator
import logging

logger = logging.getLogger(__name__)

class LanguageHandler:
    """Handles language detection and translation for incoming queries"""

    def __init__(self):
        self.translator = Translator()
        # Initialize langid with optimized parameters
        langid.set_languages(['es', 'en', 'fr', 'de', 'it', 'pt', 'ca', 'eu', 'gl'])

    def detect_and_translate(self, text: str) -> Tuple[str, str, str, Optional[str]]:
        """
        Detect language and translate to Spanish if needed
        Returns: (translated_text, original_language, confidence, error)
        """
        try:
            # Detect language
            detected_lang, confidence = langid.classify(text)
            
            # If already Spanish, return as is
            if detected_lang == 'es':
                return text, detected_lang, str(confidence), None
                
            # Translate to Spanish
            translation = self.translator.translate(text, dest='es', src=detected_lang)
            
            return translation.text, detected_lang, str(confidence), None
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            # Return original text with error
            return text, 'unknown', '0.0', str(e)

    def translate_response(self, text: str, target_lang: str) -> Tuple[str, Optional[str]]:
        """
        Translate response back to original query language
        Returns: (translated_text, error)
        """
        try:
            if target_lang == 'es':
                return text, None
                
            translation = self.translator.translate(text, dest=target_lang, src='es')
            return translation.text, None
            
        except Exception as e:
            logger.error(f"Response translation error: {str(e)}")
            return text, str(e)

    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        language_names = {
            'es': 'Spanish',
            'en': 'English',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ca': 'Catalan',
            'eu': 'Basque',
            'gl': 'Galician'
        }
        return language_names.get(lang_code, 'Unknown')