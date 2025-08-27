# Variables globales pour stocker l'analyse IA et l'état de chargement
import re


ai_analysis_cache = {}
is_analyzing = {}
analysis_results = {}

def store_ai_analysis(expected_provided_tuple, type_pattern):
    """
    Lance l'analyse IA en arrière-plan pour ne pas bloquer l'UI,
    afin que le verso s'affiche tout de suite avec un spinner.
    """
    true_answer = expected_provided_tuple[0] or ""
    user_answer = expected_provided_tuple[1] or ""

    question_text = get_current_question()
    cache_key = f"{hash(question_text)}_{hash(true_answer)}_{hash(user_answer)}"

    # Déjà en cache
    if cache_key in ai_analysis_cache:
        print(f"Using cached analysis for {cache_key}")
        return expected_provided_tuple

    # Analyse déjà en cours
    if is_analyzing.get(cache_key, False):
        print(f"Analysis already in progress for {cache_key}")
        return expected_provided_tuple

    # Marquer en cours
    is_analyzing[cache_key] = True
    analysis_results[cache_key] = None
    print(f"Starting background AI analysis for key: {cache_key}")

    # Tâche de fond
    def task():
        try:
            print("Calling AI API for analysis (background)...")
            return analyze_answer_with_ai(question_text, true_answer, user_answer)
        except Exception as e:
            print(f"AI Analysis Error (bg): {e}")
            return {"score": 5, "tips": f"Analysis error: {str(e)}", "review_suggestion": "Good"}

    # Callback: reçoit un Future
    def on_done(fut):
        try:
            result = fut.result()
        except Exception as e:
            print(f"Background task failed: {e}")
            result = {"score": 5, "tips": f"Analysis error: {str(e)}", "review_suggestion": "Good"}
        finally:
            # Toujours dé-marquer l'état d'analyse
            is_analyzing[cache_key] = False

        # Stocker le résultat (un dict, pas un Future)
        ai_analysis_cache[cache_key] = result
        analysis_results[cache_key] = result
        print(f"AI analysis completed (bg) for {cache_key}")

        # Rafraîchir l'affichage
        try:
            refresh_ai_analysis()
        except Exception as e:
            print(f"Refresh error after AI analysis: {e}")

    # Lancer en arrière-plan
    mw.taskman.run_in_background(task, on_done)

    # Laisser l'UI afficher le verso avec spinner
    return expected_provided_tuple

def clean_html_content(html_content):
    """
    Nettoie le contenu HTML pour extraire le texte brut, 
    en supprimant les balises HTML, le CSS et le JavaScript.
    """
    if not html_content:
        return ""
    
    # 1. Supprimer les blocs de script et de style
    # L'option re.DOTALL permet au '.' de correspondre aussi aux sauts de ligne
    text = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
    
    # 2. Supprimer les balises HTML restantes
    text = re.sub(r'<[^>]+>', '', text)
    
    # 3. Remplacer les entités HTML communes
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    
    # 4. Nettoyer les espaces multiples et les sauts de ligne
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def get_current_question():
    """
    **NOUVELLE FONCTION: Récupère le contenu de la question de la carte actuelle**
    """
    try:
        if hasattr(mw, 'reviewer') and mw.reviewer and hasattr(mw.reviewer, 'card') and mw.reviewer.card:
            card = mw.reviewer.card
            
            # Récupérer le contenu de la question (front de la carte)
            question_html = card.question()
            
            # Nettoyer le HTML pour extraire le texte
            question_text = clean_html_content(question_html)
            
            print(f"Current question extracted: {question_text[:100]}...")
            return question_text
        else:
            print("No current card available")
            return ""
    except Exception as e:
        print(f"Error getting current question: {e}")
        return ""



def render_enhanced_comparison(output, initial_expected, initial_provided, type_pattern):
    """
    Améliore l'affichage de la comparaison avec l'analyse IA
    """
    config = get_config()
    language = config.get("language", "english")
    texts = get_ui_texts(language)
    
    # Skip if AI is disabled
    if not config.get("enabled", True):
        return output
    
    # **MODIFIÉ: Inclure la question dans la clé de cache**
    question_text = get_current_question()
    cache_key = f"{hash(question_text)}_{hash(initial_expected)}_{hash(initial_provided)}"
    print(f"Rendering comparison for key: {cache_key}")
    
    # Vérification simplifiée - si l'analyse est en cours, afficher un message simple
    if is_analyzing.get(cache_key, False) and cache_key not in ai_analysis_cache:
        print(f"Analysis in progress for {cache_key}, showing simple loading message")
        # Message de chargement simple sans JavaScript compliqué
        # Dans render_enhanced_comparison, remplacer le spinner_output par :
        spinner_output = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto;">

            <!-- Comparaison par défaut d'Anki -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #6c757d;">
                {output}
            </div>

            <!-- Bloc chargement -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 16px; padding: 25px; margin: 20px 0; text-align: center; color: white; position: relative; overflow: hidden;">
                <div style="display: inline-flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div style="width: 26px; height: 26px; border: 3px solid rgba(255,255,255,0.35); border-top-color: #fff; border-radius: 50%; animation: aki_spin 0.9s linear infinite;"></div>
                    <div style="font-size: 18px; font-weight: 600;">{texts['analyzing']}</div>
                </div>
                <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px;">
                    {texts['please_wait']}
                </p>
                <p style="color: rgba(255,255,255,0.7); margin-top: 10px; font-size: 12px; font-style: italic;">
                    Actualisation automatique...
                </p>
            </div>

            <!-- Style + auto-refresh doux -->
            <style>
            @keyframes aki_spin {{ to {{ transform: rotate(360deg); }} }}
            </style>
            <script>
            // Relance un rafraîchissement du verso pendant l'analyse.
            // Sans boucle infinie: on appelle 1 fois à T+1.2s; si encore en cours, le même bloc se ré-affichera et relancera ce timeout.
            setTimeout(function() {{
                if (typeof pycmd === 'function') {{
                pycmd('refresh_ai_analysis');
                }}
            }}, 1200);
            </script>
        </div>
        """
        return spinner_output
    
    # Récupérer l'analyse IA stockée avec debug
    ai_analysis = analysis_results.get(cache_key) or ai_analysis_cache.get(cache_key)
    print(f"Retrieved analysis for {cache_key}: {ai_analysis is not None}")
    
    # Si l'analyse n'est pas disponible, utiliser des valeurs par défaut
    if not ai_analysis:
        print(f"No analysis available for {cache_key}, using defaults")
        ai_analysis = {
            "score": 5, 
            "tips": texts.get('ai_not_available', 'AI analysis not available'), 
            "review_suggestion": "Good"
        }
    
    # Déterminer les couleurs selon le score
    score = ai_analysis.get('score', 5)
    if score <= 3:
        score_color = "#f44336"  # Rouge
        score_bg = "#ffebee"
        score_icon = "❌"
        pulse_color = "#f44336"
    elif score <= 5:
        score_color = "#ff9800"  # Orange
        score_bg = "#fff3e0"
        score_icon = "⚠️"
        pulse_color = "#ff9800"
    elif score <= 8:
        score_color = "#4caf50"  # Vert
        score_bg = "#e8f5e8"
        score_icon = "✅"
        pulse_color = "#4caf50"
    else:
        score_color = "#2196f3"  # Bleu
        score_bg = "#e3f2fd"
        score_icon = "🌟"
        pulse_color = "#2196f3"
    
    # Déterminer la couleur de la suggestion
    suggestion = ai_analysis.get('review_suggestion', 'Good')
    suggestion_colors = {
        "Again": ("#f44336", "#ffebee", "🔄"),
        "Hard": ("#ff9800", "#fff3e0", "🔥"), 
        "Good": ("#4caf50", "#e8f5e8", "👍"),
        "Easy": ("#2196f3", "#e3f2fd", "😎")
    }
    suggestion_color, suggestion_bg, suggestion_icon = suggestion_colors.get(suggestion, ("#4caf50", "#e8f5e8", "👍"))
    
    # **NOUVEAU: Afficher la question pour plus de contexte si elle existe**
    question_display = ""
    if question_text and len(question_text.strip()) > 0:
        # Limiter la longueur de la question affichée
        display_question = question_text[:200] + "..." if len(question_text) > 200 else question_text
        question_display = f"""
        <div style="background: rgba(255,255,255,0.9); border: 2px solid #e0e0e0; border-radius: 12px; padding: 15px; margin-bottom: 15px;">
            <h4 style="color: #2c3e50; margin: 0 0 8px 0; font-size: 16px; font-weight: 700; display: flex; align-items: center;">
                ❓ {texts.get('question_context', 'Question Context')}:
            </h4>
            <p style="color: #34495e; margin: 0; line-height: 1.4; font-size: 14px; font-style: italic;">
                {display_question}
            </p>
        </div>
        """
    
    # Affichage simplifié des résultats
    enhanced_output = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto;">
        
        <!-- Comparaison par défaut d'Anki -->
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #6c757d;">
            {output}
        </div>
        
        <!-- Analyse IA avec animation d'apparition -->
        <div style="background: {score_bg}; border: 2px solid {score_color}; border-radius: 16px; padding: 25px; margin: 20px 0; box-shadow: 0 8px 32px rgba(0,0,0,0.1);">
            
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; flex: 1;">
                    <div style="background: {score_color}; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                        <span style="font-size: 20px;">🤖</span>
                    </div>
                    <h3 style="color: {score_color}; margin: 0; font-size: 22px; font-weight: 700;">
                        {texts.get('ai_analysis', 'AI Analysis')}
                    </h3>
                </div>
                <div style="background: linear-gradient(135deg, {score_color}, {score_color}dd); color: white; padding: 12px 20px; border-radius: 25px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    {score_icon} {score}/10
                </div>
            </div>
            
            {question_display}
            
            <div style="margin-bottom: 20px; padding: 15px; background: rgba(255,255,255,0.7); border-radius: 12px; border-left: 4px solid {score_color};">
                <h4 style="color: #2c3e50; margin: 0 0 10px 0; font-size: clamp(15px, 4vw, 17px); font-weight: 700; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center;">
                    💡 {texts.get('improvement_tips', 'Improvement Tips')}
                </h4>
                <p style="color: #34495e; margin: 0; line-height: 1.6; font-size: clamp(14px, 4vw, 16px);">
                    {ai_analysis.get('tips', texts.get('no_tips_available', 'No tips available'))}
                </p>
            </div>
            
            <div style="background: linear-gradient(135deg, {suggestion_bg}, {suggestion_bg}dd); border: 2px solid {suggestion_color}; border-radius: 12px; padding: 16px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span style="color: #2c3e50; font-weight: 700; font-size: 16px; display: flex; align-items: center;">
                        🎯 {texts.get('review_suggestion', 'Review Suggestion')}:
                    </span>
                    <span style="background: linear-gradient(135deg, {suggestion_color}, {suggestion_color}dd); color: white; padding: 10px 18px; border-radius: 20px; font-weight: bold; font-size: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
                        {suggestion_icon} {texts.get('suggestions', {}).get(suggestion, suggestion)}
                    </span>
                </div>
            </div>
        </div>
    </div>
    """
    
    # Nettoyer les caches plus prudemment
    cleanup_old_cache_entries()
    
    return enhanced_output

def cleanup_old_cache_entries():
    """Nettoie les anciennes entrées de cache"""
    try:
        if len(ai_analysis_cache) > 10:
            # Garder seulement les 5 plus récents
            keys_to_remove = list(ai_analysis_cache.keys())[:-5]
            for key in keys_to_remove:
                ai_analysis_cache.pop(key, None)
                is_analyzing.pop(key, None)
                analysis_results.pop(key, None)
            print(f"Cleaned up {len(keys_to_remove)} old cache entries")
    except Exception as e:
        print(f"Error during cache cleanup: {e}")

def debug_cache_state():
    """Debug la situation actuelle des caches"""
    print("=== CACHE STATE DEBUG ===")
    print(f"ai_analysis_cache: {len(ai_analysis_cache)} entries")
    print(f"is_analyzing: {len(is_analyzing)} entries")
    print(f"analysis_results: {len(analysis_results)} entries")
    print(f"Currently analyzing: {[k for k, v in is_analyzing.items() if v]}")
    print("========================")

def reset_ai_caches():
    """Réinitialise tous les caches"""
    global ai_analysis_cache, is_analyzing, analysis_results
    ai_analysis_cache.clear()
    is_analyzing.clear()
    analysis_results.clear()
    print("AI caches reset")

# import the necessary hooks
from aqt import gui_hooks, mw
from aqt.utils import showInfo, showWarning
import json
import urllib.request
import urllib.error

# Configuration par défaut
DEFAULT_CONFIG = {
    "provider": "openai",
    "language": "english",
    "openai_api_key": "",
    "openai_model": "gpt-3.5-turbo",
    "gemini_api_key": "",
    "gemini_model": "gemini-1.5-flash",
    "claude_api_key": "",
    "claude_model": "claude-3-haiku-20240307",
    "deepseek_api_key": "",
    "deepseek_model": "deepseek-chat",
    "groq_api_key": "",
    "groq_model": "llama3-8b-8192",
    "openrouter_api_key": "",
    "openrouter_model": "deepseek/deepseek-r1:free",
    "enabled": True,
    "max_tokens": 200,
    "temperature": 0.7
}

# **MODIFIÉ: Langues supportées avec nouveau texte pour le contexte de question**
LANGUAGES = {
    "english": {
        "name": "English",
        "ai_analysis": "AI Analysis",
        "improvement_tips": "Improvement Tips",
        "review_suggestion": "Review Suggestion",
        "question_context": "Question Context",
        "analyzing": "AI Analysis in progress...",
        "please_wait": "Please wait while the AI evaluates your answer",
        "processing_response": "Processing your response...",
        "ai_not_available": "AI analysis not available",
        "no_tips_available": "No tips available",
        "suggestions": {
            "Again": "Again",
            "Hard": "Hard", 
            "Good": "Good",
            "Easy": "Easy"
        }
    },
    "french": {
        "name": "Français",
        "ai_analysis": "Analyse IA",
        "improvement_tips": "Conseils d'amélioration",
        "review_suggestion": "Suggestion de révision",
        "question_context": "Contexte de la question",
        "analyzing": "Analyse IA en cours...",
        "please_wait": "Veuillez patienter pendant que l'IA évalue votre réponse",
        "processing_response": "Traitement de votre réponse...",
        "ai_not_available": "Analyse IA non disponible",
        "no_tips_available": "Aucun conseil disponible",
        "suggestions": {
            "Again": "Encore",
            "Hard": "Difficile", 
            "Good": "Correct",
            "Easy": "Facile"
        }
    },
    "spanish": {
        "name": "Español",
        "ai_analysis": "Análisis IA",
        "improvement_tips": "Consejos de mejora",
        "review_suggestion": "Sugerencia de revisión",
        "question_context": "Contexto de la pregunta",
        "analyzing": "Análisis IA en progreso...",
        "please_wait": "Por favor espera mientras la IA evalúa tu respuesta",
        "processing_response": "Procesando tu respuesta...",
        "ai_not_available": "Análisis IA no disponible",
        "no_tips_available": "Sin consejos disponibles",
        "suggestions": {
            "Again": "De nuevo",
            "Hard": "Difícil", 
            "Good": "Bien",
            "Easy": "Fácil"
        }
    },
    "german": {
        "name": "Deutsch",
        "ai_analysis": "KI-Analyse",
        "improvement_tips": "Verbesserungstipps",
        "review_suggestion": "Wiederholungsvorschlag",
        "question_context": "Fragenkontext",
        "analyzing": "KI-Analyse läuft...",
        "please_wait": "Bitte warten Sie, während die KI Ihre Antwort bewertet",
        "processing_response": "Ihre Antwort wird verarbeitet...",
        "ai_not_available": "KI-Analyse nicht verfügbar",
        "no_tips_available": "Keine Tipps verfügbar",
        "suggestions": {
            "Again": "Nochmal",
            "Hard": "Schwer", 
            "Good": "Gut",
            "Easy": "Einfach"
        }
    }
}

def get_ui_texts(language="english"):
    """Récupère les textes de l'interface selon la langue"""
    return LANGUAGES.get(language, LANGUAGES["english"])

# Configuration des fournisseurs
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "url": "https://api.openai.com/v1/chat/completions",
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
        "headers_func": lambda api_key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    },
    "gemini": {
        "name": "Google Gemini",
        "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
        "headers_func": lambda api_key: {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
    },
    "claude": {
        "name": "Anthropic Claude",
        "url": "https://api.anthropic.com/v1/messages",
        "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
        "headers_func": lambda api_key: {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    },
    "deepseek": {
        "name": "DeepSeek",
        "url": "https://api.deepseek.com/chat/completions",
        "models": ["deepseek-chat", "deepseek-coder"],
        "headers_func": lambda api_key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    },
    "groq": {
        "name": "Groq",
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "models": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
        "headers_func": lambda api_key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    },
    "openrouter": {
        "name": "OpenRouter",
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "models": ["deepseek/deepseek-r1:free","google/gemini-2.5-flash","openai/gpt-4o-mini-2024-07-18", "meta-llama/llama-3.2-1b-instruct", "arliai/qwq-32b-arliai-rpr-v1","openai/gpt-oss-20b:free", "qwen/qwen3-coder:free" ,"google/gemma-3n-e2b-it:free" ,"tencent/hunyuan-a13b-instruct:free"],
        "headers_func": lambda api_key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    }
}

def get_config():
    """Récupère la configuration depuis les métadonnées d'Anki"""
    try:
        config = mw.addonManager.getConfig(__name__)
        if not config:
            config = DEFAULT_CONFIG
            save_config(config)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    """Sauvegarde la configuration dans les métadonnées d'Anki"""
    try:
        mw.addonManager.writeConfig(__name__, config)
    except Exception as e:
        print(f"Error saving config: {e}")

def format_messages_for_provider(messages, provider):
    """Formate les messages selon le fournisseur"""
    if provider == "gemini":
        # Gemini utilise un format différent
        formatted_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # Gemini n'a pas de role system, on l'ajoute au premier message user
                continue
            elif msg["role"] == "user":
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
                content = f"{system_msg}\n\n{msg['content']}" if system_msg else msg["content"]
                formatted_messages.append({
                    "parts": [{"text": content}]
                })
        return {"contents": formatted_messages}
    
    elif provider == "claude":
        # Claude utilise un format spécifique
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_messages = [m for m in messages if m["role"] != "system"]
        
        formatted_data = {
            "model": "",  # Sera ajouté plus tard
            "max_tokens": 350,  # Sera ajouté plus tard
            "messages": user_messages
        }
        
        if system_msg:
            formatted_data["system"] = system_msg
            
        return formatted_data
    
    else:
        # Format OpenAI (compatible avec OpenAI, DeepSeek, Groq)
        return {
            "messages": messages,
            "max_tokens": 350,  # Sera ajouté plus tard
            "temperature": 0.7  # Sera ajouté plus tard
        }

def call_ai_api(messages, provider="openai", model="gpt-3.5-turbo", max_tokens=200, temperature=0.7, api_key=""):
    """
    Appelle l'API du fournisseur choisi
    """
    if provider not in PROVIDERS:
        raise Exception(f"Fournisseur non supporté: {provider}")
    
    provider_config = PROVIDERS[provider]
    
    # Construire l'URL
    if provider == "gemini":
        url = provider_config["url"].format(model=model) + f"?key={api_key}"
        headers = {"Content-Type": "application/json"}
    else:
        url = provider_config["url"]
        headers = provider_config["headers_func"](api_key)
    
    # Formater les données selon le fournisseur
    data = format_messages_for_provider(messages, provider)
    
    # Ajouter les paramètres spécifiques au modèle
    if provider == "gemini":
        data["generationConfig"] = {
            "maxOutputTokens": max_tokens,
            "temperature": temperature
        }
    elif provider == "claude":
        data["model"] = model
        data["max_tokens"] = max_tokens
        data["temperature"] = temperature
    else:
        # OpenAI, DeepSeek, Groq
        data["model"] = model
        data["max_tokens"] = max_tokens
        data["temperature"] = temperature
    
    try:
        # Préparer la requête
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
        
        # Faire la requête
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            print(f'--AI response-- {response_data}')
        
        # Extraire la réponse selon le fournisseur
        if provider == "gemini":
            if 'candidates' in response_data and len(response_data['candidates']) > 0:
                return response_data['candidates'][0]['content']['parts'][0]['text']
        elif provider == "claude":
            if 'content' in response_data and len(response_data['content']) > 0:
                return response_data['content'][0]['text']
        else:
            # OpenAI, DeepSeek, Groq
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
        
        raise Exception("Réponse API invalide")
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            if provider == "gemini":
                error_message = error_data.get('error', {}).get('message', str(e))
            elif provider == "claude":
                error_message = error_data.get('error', {}).get('message', str(e))
            else:
                error_message = error_data.get('error', {}).get('message', str(e))
        except:
            error_message = f"Erreur HTTP {e.code}: {error_body[:100]}"
        raise Exception(f"Erreur API {provider_config['name']}: {error_message}")
    
    except urllib.error.URLError as e:
        raise Exception(f"Erreur de connexion: {str(e)}")
    
    except json.JSONDecodeError as e:
        raise Exception(f"Erreur de parsing JSON: {str(e)}")
    
    except Exception as e:
        raise Exception(f"Erreur inattendue: {str(e)}")

def get_language_specific_prompt(language, question_text, true_answer, user_answer):
    """
    **MODIFIÉ: Génère un prompt selon la langue configurée avec contexte de question**
    """
    
    prompts = {
        "english": f"""
        Analyze the student's answer in the context of the given question and provide a structured evaluation.

        Question: "{question_text}"
        Expected answer: "{true_answer}"
        Student's answer: "{user_answer}"

        Please provide your evaluation in the following JSON format:
        {{
            "score": [number from 0 to 10],
            "tips": "[constructive feedback in English, maximum 100 words, considering the question context]",
            "review_suggestion": "[choose from: Again, Hard, Good, Easy]"
        }}

        Evaluation criteria:
        - Score 0-3: Incorrect or very incomplete answer → "Again"
        - Score 4-5: Partially correct but with significant errors → "Hard"  
        - Score 6-8: Correct answer with minor imperfections → "Good"
        - Score 9-10: Excellent and complete answer → "Easy"
        
        Consider the question context when evaluating the relevance and completeness of the student's response.
        """,
        
        "french": f"""
        Analysez la réponse de l'étudiant dans le contexte de la question donnée et fournissez une évaluation structurée.

        Question: "{question_text}"
        Réponse attendue: "{true_answer}"
        Réponse de l'étudiant: "{user_answer}"

        Veuillez fournir votre évaluation au format JSON suivant:
        {{
            "score": [nombre de 0 à 10],
            "tips": "[conseils constructifs en français, maximum 100 mots, en tenant compte du contexte de la question]",
            "review_suggestion": "[choisir parmi: Again, Hard, Good, Easy]"
        }}

        Critères d'évaluation:
        - Score 0-3: Réponse incorrecte ou très incomplète → "Again"
        - Score 4-5: Réponse partiellement correcte mais avec des erreurs importantes → "Hard"  
        - Score 6-8: Réponse correcte avec quelques imperfections mineures → "Good"
        - Score 9-10: Réponse excellente et complète → "Easy"
        
        Considérez le contexte de la question lors de l'évaluation de la pertinence et de la complétude de la réponse de l'étudiant.
        """,
        
        "spanish": f"""
        Analiza la respuesta del estudiante en el contexto de la pregunta dada y proporciona una evaluación estructurada.

        Pregunta: "{question_text}"
        Respuesta esperada: "{true_answer}"
        Respuesta del estudiante: "{user_answer}"

        Por favor proporciona tu evaluación en el siguiente formato JSON:
        {{
            "score": [número del 0 al 10],
            "tips": "[comentarios constructivos en español, máximo 100 palabras, considerando el contexto de la pregunta]",
            "review_suggestion": "[elegir entre: Again, Hard, Good, Easy]"
        }}

        Criterios de evaluación:
        - Puntuación 0-3: Respuesta incorrecta o muy incompleta → "Again"
        - Puntuación 4-5: Respuesta parcialmente correcta pero con errores significativos → "Hard"
        - Puntuación 6-8: Respuesta correcta con imperfecciones menores → "Good"
        - Puntuación 9-10: Respuesta excelente y completa → "Easy"
        
        Considera el contexto de la pregunta al evaluar la relevancia y completitud de la respuesta del estudiante.
        """,
        
        "german": f"""
        Analysieren Sie die Antwort des Studenten im Kontext der gegebenen Frage und geben Sie eine strukturierte Bewertung ab.

        Frage: "{question_text}"
        Erwartete Antwort: "{true_answer}"
        Antwort des Studenten: "{user_answer}"

        Bitte geben Sie Ihre Bewertung im folgenden JSON-Format an:
        {{
            "score": [Zahl von 0 bis 10],
            "tips": "[konstruktives Feedback auf Deutsch, maximal 100 Wörter, unter Berücksichtigung des Fragenkontexts]",
            "review_suggestion": "[wählen Sie aus: Again, Hard, Good, Easy]"
        }}

        Bewertungskriterien:
        - Punktzahl 0-3: Falsche oder sehr unvollständige Antwort → "Again"
        - Punktzahl 4-5: Teilweise richtige Antwort, aber mit erheblichen Fehlern → "Hard"
        - Punktzahl 6-8: Richtige Antwort mit kleineren Unvollkommenheiten → "Good"
        - Punktzahl 9-10: Ausgezeichnete und vollständige Antwort → "Easy"
        
        Berücksichtigen Sie den Fragenkontext bei der Bewertung der Relevanz und Vollständigkeit der studentischen Antwort.
        """
    }
    
    return prompts.get(language, prompts["english"])

def analyze_answer_with_ai(question_text: str, true_answer: str, user_answer: str) -> dict:
    """
    **MODIFIÉ: Analyse la réponse de l'utilisateur avec l'IA en incluant le contexte de la question**
    Retourne un dictionnaire avec le score, les conseils et la suggestion de révision
    """
    config = get_config()
    
    if not config.get("enabled", True):
        return {"score": 5, "tips": "IA désactivée", "review_suggestion": "Good"}
    
    provider = config.get("provider", "openai")
    language = config.get("language", "english")
    api_key_field = f"{provider}_api_key"
    model_field = f"{provider}_model"
    
    api_key = config.get(api_key_field, "").strip()
    if not api_key:
        return {"score": 5, "tips": f"Clé API {PROVIDERS[provider]['name']} non configurée", "review_suggestion": "Good"}
    
    # **MODIFIÉ: Utiliser le prompt avec contexte de question selon la langue configurée**
    prompt = get_language_specific_prompt(language, question_text, true_answer, user_answer)
    
    # Message système selon la langue
    system_messages = {
        "english": "You are an educational assistant that evaluates student responses constructively and kindly. Use the question context to provide more accurate and relevant feedback.",
        "french": "Vous êtes un assistant pédagogique qui évalue les réponses des étudiants de manière constructive et bienveillante. Utilisez le contexte de la question pour fournir des commentaires plus précis et pertinents.",
        "spanish": "Eres un asistente educativo que evalúa las respuestas de los estudiantes de manera constructiva y amable. Usa el contexto de la pregunta para proporcionar comentarios más precisos y relevantes.",
        "german": "Sie sind ein pädagogischer Assistent, der die Antworten der Studenten konstruktiv und freundlich bewertet. Nutzen Sie den Fragenkontext, um genauere und relevantere Rückmeldungen zu geben."
    }
    
    system_message = system_messages.get(language, system_messages["english"])

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ]

    try:
        ai_response = call_ai_api(
            messages=messages,
            provider=provider,
            model=config.get(model_field, PROVIDERS[provider]["models"][0]),
            max_tokens=config.get("max_tokens", 200),
            temperature=config.get("temperature", 0.7),
            api_key=api_key
        )
        
        # Tenter de parser la réponse JSON
        try:
            # Nettoyer la réponse (enlever les balises markdown si présentes)
            clean_response = ai_response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            result = json.loads(clean_response)
            # Valider les champs requis
            if all(key in result for key in ["score", "tips", "review_suggestion"]):
                # Valider le score
                result["score"] = max(0, min(10, int(result["score"])))
                # Valider la suggestion de révision
                if result["review_suggestion"] not in ["Again", "Hard", "Good", "Easy"]:
                    result["review_suggestion"] = "Good"
                return result
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        # Si le parsing JSON échoue, essayer d'extraire les informations
        lines = ai_response.split('\n')
        score = 5
        tips = "Analyse disponible dans la réponse complète"
        review_suggestion = "Good"
        
        for line in lines:
            if 'score' in line.lower():
                try:
                    import re
                    score_match = re.search(r'(\d+)', line)
                    if score_match:
                        score = max(0, min(10, int(score_match.group(1))))
                except:
                    pass
        
        return {"score": score, "tips": ai_response[:300] + "...", "review_suggestion": review_suggestion}
        
    except Exception as e:
        print(f"AI Analysis Error: {str(e)}")  # Pour debugging
        return {"score": 5, "tips": f"Erreur d'analyse {PROVIDERS[provider]['name']}: {str(e)}", "review_suggestion": "Good"}

def setup_config_menu():
    """Configure le menu de configuration"""
    def open_config():
        config = get_config()
        
        # Interface simple pour la configuration
        from aqt.qt import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QSpinBox, QDoubleSpinBox, QTabWidget, QWidget
        
        dialog = QDialog(mw)
        dialog.setWindowTitle("Configuration IA Multi-Fournisseurs")
        dialog.setMinimumWidth(550)
        dialog.setMinimumHeight(700)
        
        layout = QVBoxLayout()
        
        # Paramètres généraux en haut
        general_group = QVBoxLayout()
        
        # Sélecteur de fournisseur principal
        provider_layout = QHBoxLayout()
        provider_layout.addWidget(QLabel("AI Provider:"))
        provider_combo = QComboBox()
        provider_items = [(key, value["name"]) for key, value in PROVIDERS.items()]
        for key, name in provider_items:
            provider_combo.addItem(name, key)
        
        current_provider = config.get("provider", "openai")
        provider_index = next((i for i, (key, _) in enumerate(provider_items) if key == current_provider), 0)
        provider_combo.setCurrentIndex(provider_index)
        provider_layout.addWidget(provider_combo)
        general_group.addLayout(provider_layout)
        
        # Sélecteur de langue
        language_layout = QHBoxLayout()
        language_layout.addWidget(QLabel("Language:"))
        language_combo = QComboBox()
        for lang_key, lang_info in LANGUAGES.items():
            language_combo.addItem(lang_info["name"], lang_key)
        
        current_language = config.get("language", "english")
        language_index = next((i for i, (key, _) in enumerate(LANGUAGES.items()) if key == current_language), 0)
        language_combo.setCurrentIndex(language_index)
        language_layout.addWidget(language_combo)
        general_group.addLayout(language_layout)
        
        # Activation
        enabled_checkbox = QCheckBox("Enable AI Analysis")
        enabled_checkbox.setChecked(config.get("enabled", True))
        general_group.addWidget(enabled_checkbox)
        
        # Max tokens
        tokens_layout = QHBoxLayout()
        tokens_layout.addWidget(QLabel("Max tokens:"))
        tokens_spin = QSpinBox()
        tokens_spin.setRange(50, 4000)
        tokens_spin.setValue(config.get("max_tokens", 200))
        tokens_layout.addWidget(tokens_spin)
        general_group.addLayout(tokens_layout)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature (0-1):"))
        temp_spin = QDoubleSpinBox()
        temp_spin.setRange(0.0, 1.0)
        temp_spin.setSingleStep(0.1)
        temp_spin.setValue(config.get("temperature", 0.7))
        temp_layout.addWidget(temp_spin)
        general_group.addLayout(temp_layout)
        
        layout.addLayout(general_group)
        
        # Onglets pour chaque fournisseur
        tabs = QTabWidget()
        
        # Stockage des widgets pour récupérer les valeurs
        api_inputs = {}
        model_combos = {}
        tab_widgets = {}
        
        for provider_key, provider_info in PROVIDERS.items():
            tab = QWidget()
            tab_layout = QVBoxLayout()
            
            # Clé API
            api_key_layout = QHBoxLayout()
            api_key_layout.addWidget(QLabel(f"{provider_info['name']} API Key:"))
            api_key_input = QLineEdit(config.get(f"{provider_key}_api_key", ""))
            
            # Compatible avec PyQt5 et PyQt6 pour le mode password
            try:
                api_key_input.setEchoMode(QLineEdit.EchoMode.Password)  # PyQt6
            except AttributeError:
                try:
                    api_key_input.setEchoMode(QLineEdit.Password)  # PyQt5
                except AttributeError:
                    api_key_input.setEchoMode(2)  # Fallback numérique
            
            api_key_layout.addWidget(api_key_input)
            tab_layout.addLayout(api_key_layout)
            api_inputs[provider_key] = api_key_input
            
            # Modèle
            model_layout = QHBoxLayout()
            model_layout.addWidget(QLabel("Model:"))
            model_combo = QComboBox()
            model_combo.addItems(provider_info["models"])
            current_model = config.get(f"{provider_key}_model", provider_info["models"][0])
            if current_model in provider_info["models"]:
                model_combo.setCurrentText(current_model)
            model_layout.addWidget(model_combo)
            tab_layout.addLayout(model_layout)
            model_combos[provider_key] = model_combo
            
            # Instructions spécifiques au fournisseur
            instructions = {
                "openai": "Get your API key at: https://platform.openai.com/api-keys",
                "gemini": "Get your API key at: https://aistudio.google.com/app/apikey",
                "claude": "Get your API key at: https://console.anthropic.com/",
                "deepseek": "Get your API key at: https://platform.deepseek.com/api_keys",
                "groq": "Get your API key at: https://console.groq.com/keys",
                "openrouter": "Get your API key at: https://openrouter.ai/settings/keys"
            }
            
            info_label = QLabel(instructions.get(provider_key, ""))
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #666; font-size: 11px; margin: 10px 0;")
            tab_layout.addWidget(info_label)
            
            tab.setLayout(tab_layout)
            tabs.addTab(tab, provider_info["name"])
            tab_widgets[provider_key] = tab
        
        layout.addWidget(tabs)
        
        # Fonction pour activer/désactiver les onglets selon le fournisseur sélectionné
        def update_tab_states():
            selected_provider = provider_combo.currentData()
            for i, (provider_key, _) in enumerate(PROVIDERS.items()):
                tab_enabled = (provider_key == selected_provider)
                tabs.setTabEnabled(i, tab_enabled)
                if tab_enabled:
                    tabs.setCurrentIndex(i)
        
        # Connecter le changement de fournisseur à la mise à jour des onglets
        provider_combo.currentTextChanged.connect(update_tab_states)
        
        # Initialiser l'état des onglets
        update_tab_states()
        
        # Test de connexion
        test_button = QPushButton("Test API Connection")
        layout.addWidget(test_button)
        
        def test_api():
            current_provider_data = provider_combo.currentData()
            api_key = api_inputs[current_provider_data].text().strip()
            
            if not api_key:
                showWarning("Please enter an API key to test the connection.")
                return
            
            # Changer le texte du bouton pour indiquer le test en cours
            original_text = test_button.text()
            test_button.setText("Testing...")
            test_button.setEnabled(False)
            
            try:
                messages = [{"role": "user", "content": "Respond simply 'OK' to test the connection."}]
                response = call_ai_api(
                    messages=messages,
                    provider=current_provider_data,
                    model=model_combos[current_provider_data].currentText(),
                    max_tokens=10,
                    temperature=0.1,
                    api_key=api_key
                )
                showInfo(f"✅ Connection successful with {PROVIDERS[current_provider_data]['name']}!\n\nResponse: {response[:50]}...")
            except Exception as e:
                showWarning(f"❌ Connection error with {PROVIDERS[current_provider_data]['name']}:\n\n{str(e)}")
            finally:
                # Restaurer le bouton
                test_button.setText(original_text)
                test_button.setEnabled(True)
        
        test_button.clicked.connect(test_api)
        
        # Boutons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        def save_and_close():
            new_config = {
                "provider": provider_combo.currentData(),
                "language": language_combo.currentData(),
                "enabled": enabled_checkbox.isChecked(),
                "max_tokens": tokens_spin.value(),
                "temperature": temp_spin.value()
            }
            
            # Sauvegarder toutes les clés API et modèles
            for provider_key in PROVIDERS.keys():
                new_config[f"{provider_key}_api_key"] = api_inputs[provider_key].text()
                new_config[f"{provider_key}_model"] = model_combos[provider_key].currentText()
            
            save_config(new_config)
            showInfo("Configuration saved!")
            dialog.accept()
        
        save_button.clicked.connect(save_and_close)
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.setLayout(layout)
        
        # Compatible avec PyQt5 et PyQt6 pour l'exécution
        try:
            dialog.exec()  # PyQt6
        except AttributeError:
            dialog.exec_()  # PyQt5
    
    # Ajouter au menu Tools
    action = mw.form.menuTools.addAction("AI Multi-Provider Configuration")
    action.triggered.connect(open_config)

# Commande pour rafraîchir l'analyse IA
def refresh_ai_analysis():
    """Rafraîchit l'affichage de l'analyse IA"""
    if hasattr(mw, 'reviewer') and mw.reviewer and hasattr(mw.reviewer, 'card') and mw.reviewer.card:
        if hasattr(mw.reviewer, '_showAnswer'):
            mw.reviewer._showAnswer()

# Enregistrer la commande pour le JavaScript
def register_refresh_command():
    """Enregistre la commande de rafraîchissement pour le JavaScript"""
    try:
        from aqt import gui_hooks
        gui_hooks.webview_did_receive_js_message.append(handle_js_message)
    except ImportError:
        pass

def handle_js_message(handled, message, context):
    """Gère les messages JavaScript"""
    if message == "refresh_ai_analysis":
        refresh_ai_analysis()
        return True, None
    return handled

# Initialisation
def init():
    """Initialise l'add-on"""
    setup_config_menu()
    register_refresh_command()
    
    # Nettoyer les caches au démarrage
    ai_analysis_cache.clear()
    is_analyzing.clear()
    analysis_results.clear()

# Add the functions to the hooks
gui_hooks.reviewer_will_compare_answer.append(store_ai_analysis)
gui_hooks.reviewer_will_render_compared_answer.append(render_enhanced_comparison)

# Initialiser lors du chargement
init()