# Variables globales pour stocker l'analyse IA et l'état de chargement
ai_analysis_cache = {}
is_analyzing = {}
analysis_results = {}

def store_ai_analysis(expected_provided_tuple, type_pattern):
    """
    Analyse la réponse avec l'IA et stocke le résultat
    """
    true_answer = expected_provided_tuple[0] or ""
    user_answer = expected_provided_tuple[1] or ""
    
    # Créer une clé unique pour cette comparaison
    cache_key = f"{hash(true_answer)}_{hash(user_answer)}"
    
    # Vérifier si l'analyse existe déjà
    if cache_key in ai_analysis_cache:
        return expected_provided_tuple
    
    # Marquer comme en cours d'analyse
    is_analyzing[cache_key] = True
    analysis_results[cache_key] = None
    
    # Lancer l'analyse en arrière-plan
    import threading
    
    def analyze_in_background():
        try:
            ai_analysis = analyze_answer_with_ai(true_answer, user_answer)
            analysis_results[cache_key] = ai_analysis
            ai_analysis_cache[cache_key] = ai_analysis
            
            # Force refresh the UI after analysis is complete
            from aqt import mw
            if hasattr(mw, 'reviewer') and mw.reviewer and hasattr(mw.reviewer, 'card') and mw.reviewer.card:
                # Schedule UI update on main thread
                def update_ui():
                    if hasattr(mw.reviewer, '_showAnswer'):
                        mw.reviewer._showAnswer()
                
                # Use QTimer for thread-safe UI updates
                from aqt.qt import QTimer
                QTimer.singleShot(100, update_ui)
                
        except Exception as e:
            # En cas d'erreur, stocker un résultat par défaut
            default_result = {"score": 5, "tips": f"Analysis error: {str(e)}", "review_suggestion": "Good"}
            analysis_results[cache_key] = default_result
            ai_analysis_cache[cache_key] = default_result
            print(f"AI Analysis Error: {str(e)}")  # Pour debugging
        finally:
            is_analyzing[cache_key] = False
    
    # Démarrer l'analyse en arrière-plan
    thread = threading.Thread(target=analyze_in_background, daemon=True)
    thread.start()
    
    # Retourner les réponses inchangées pour la comparaison normale
    return expected_provided_tuple

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
    
    # Créer la clé de cache
    cache_key = f"{hash(initial_expected)}_{hash(initial_provided)}"
    
    # Vérifier si l'analyse est en cours
    if is_analyzing.get(cache_key, False) and cache_key not in ai_analysis_cache:
        # Afficher le loader avec auto-refresh amélioré
        spinner_output = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto;">
            
            <!-- Comparaison par défaut d'Anki -->
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #6c757d;">
                {output}
            </div>
            
            <!-- Loader animé -->
            <div id="ai-loader-{abs(hash(cache_key))}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 16px; padding: 25px; margin: 20px 0; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.1); position: relative; overflow: hidden;">
                
                <!-- Animation de fond -->
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%); animation: shimmer 2s infinite; transform: translateX(-100%);"></div>
                
                <!-- Contenu principal -->
                <div style="position: relative; z-index: 2;">
                    <!-- Spinner principal -->
                    <div style="display: inline-block; margin-bottom: 20px;">
                        <div style="width: 50px; height: 50px; border: 4px solid rgba(255,255,255,0.3); border-top: 4px solid white; border-radius: 50%; animation: spin 1.2s linear infinite; margin: 0 auto;"></div>
                    </div>
                    
                    <!-- Points animés -->
                    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 15px;">
                        <div style="width: 8px; height: 8px; background: white; border-radius: 50%; margin: 0 3px; animation: bounce 1.4s infinite; animation-delay: 0s;"></div>
                        <div style="width: 8px; height: 8px; background: white; border-radius: 50%; margin: 0 3px; animation: bounce 1.4s infinite; animation-delay: 0.2s;"></div>
                        <div style="width: 8px; height: 8px; background: white; border-radius: 50%; margin: 0 3px; animation: bounce 1.4s infinite; animation-delay: 0.4s;"></div>
                    </div>
                    
                    <h3 style="color: white; margin: 0 0 8px 0; font-size: 20px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                        🤖 {texts['analyzing']}
                    </h3>
                    <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 14px; text-shadow: 0 1px 2px rgba(0,0,0,0.3);">
                        {texts['please_wait']}
                    </p>
                    
                    <!-- Barre de progression simulée -->
                    <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; margin: 20px 0 10px 0; overflow: hidden;">
                        <div style="height: 100%; background: linear-gradient(90deg, white, rgba(255,255,255,0.8), white); border-radius: 2px; animation: progress 3s ease-in-out infinite; width: 0%;"></div>
                    </div>
                    
                    <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 12px; font-style: italic;">
                        {texts.get('processing_response', 'Processing your response...')}
                    </p>
                </div>
            </div>
            
            <style>
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                
                @keyframes bounce {{
                    0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
                    40% {{ transform: translateY(-10px); }}
                    60% {{ transform: translateY(-5px); }}
                }}
                
                @keyframes shimmer {{
                    0% {{ transform: translateX(-100%); }}
                    100% {{ transform: translateX(100%); }}
                }}
                
                @keyframes progress {{
                    0% {{ width: 0%; transform: translateX(-100%); }}
                    50% {{ width: 70%; transform: translateX(0%); }}
                    100% {{ width: 100%; transform: translateX(100%); }}
                }}
            </style>
            
            <script>
                (function() {{
                    let refreshCount = 0;
                    const maxRefresh = 15; // Maximum ~30 secondes
                    const checkInterval = 2000; // NOUVEAU : On vérifie toutes les 2 secondes, pas toutes les secondes.
                    
                    // On utilise un ID unique pour notre minuteur pour éviter les conflits
                    const timerId = `ai_checker_${{Math.random().toString(36).substr(2, 9)}}`;

                    function checkAnalysisStatus() {{
                        // Condition d'arrêt n°1 : Le spinner n'existe plus (car il a été remplacé par le résultat)
                        const loader = document.getElementById('ai-loader-{abs(hash(cache_key))}');
                        if (!loader) {{
                            console.log('AI analysis result loaded. Stopping backup refresh.');
                            clearTimeout(window[timerId]); // On nettoie le minuteur
                            return;
                        }}

                        refreshCount++;
                        console.log('Checking AI analysis status (backup)... attempt', refreshCount);
                        
                        // Condition d'arrêt n°2 : On a atteint le nombre maximum d'essais
                        if (refreshCount > maxRefresh) {{
                            console.log('AI analysis timeout reached');
                            if (loader) {{
                                loader.innerHTML = '<div style="color: white; text-align: center; padding: 20px;">Analysis timeout. Please try again.</div>';
                            }}
                            clearTimeout(window[timerId]); // On nettoie le minuteur
                            return;
                        }}
                        
                        // On déclenche le rafraîchissement via pycmd
                        try {{
                            if (typeof pycmd !== 'undefined') {{
                                pycmd('ans');
                            }}
                        }} catch (e) {{
                            console.log('Refresh method failed:', e);
                        }}

                        // On planifie la prochaine vérification
                        // La boucle s'arrêtera d'elle-même si les conditions d'arrêt sont remplies
                        window[timerId] = setTimeout(checkAnalysisStatus, checkInterval);
                    }}
                    
                    // On démarre la vérification de secours après 2.5 secondes
                    // pour laisser une chance au rafraîchissement Python de s'exécuter en premier.
                    window[timerId] = setTimeout(checkAnalysisStatus, 2500);
                }})();
            </script>
        </div>
        """
        return spinner_output
    
    # Récupérer l'analyse IA stockée
    ai_analysis = analysis_results.get(cache_key) or ai_analysis_cache.get(cache_key)
    
    # Si l'analyse n'est pas encore disponible, utiliser des valeurs par défaut
    if not ai_analysis:
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
    
    # Créer l'affichage amélioré avec animation d'apparition
    enhanced_output = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto;">
        
        <!-- Comparaison par défaut d'Anki -->
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #6c757d;">
            {output}
        </div>
        
        <!-- Analyse IA avec animation d'apparition -->
        <div style="background: {score_bg}; border: 2px solid {score_color}; border-radius: 16px; padding: 25px; margin: 20px 0; box-shadow: 0 8px 32px rgba(0,0,0,0.1); animation: slideInUp 0.6s ease-out, pulse-border 2s infinite; position: relative; overflow: hidden;">
            
            <!-- Animation de succès -->
            <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, {pulse_color}20 0%, transparent 70%); animation: success-ripple 1s ease-out; pointer-events: none;"></div>
            
            <!-- Contenu principal -->
            <div style="position: relative; z-index: 2;">
                <div style="display: flex; align-items: center; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; flex: 1;">
                        <div style="background: {score_color}; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                            <span style="font-size: 20px;">🤖</span>
                        </div>
                        <h3 style="color: {score_color}; margin: 0; font-size: 22px; font-weight: 700; text-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            {texts.get('ai_analysis', 'AI Analysis')}
                        </h3>
                    </div>
                    <div style="background: linear-gradient(135deg, {score_color}, {score_color}dd); color: white; padding: 12px 20px; border-radius: 25px; font-weight: bold; font-size: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); animation: score-pop 0.5s ease-out 0.3s both;">
                        {score_icon} {score}/10
                    </div>
                </div>
                
                <div style="margin-bottom: 20px; padding: 15px; background: rgba(255,255,255,0.7); border-radius: 12px; border-left: 4px solid {score_color};">
                    <h4 style="color: #2c3e50; margin: 0 0 10px 0; font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center;">
                        💡 {texts.get('improvement_tips', 'Improvement Tips')}
                    </h4>
                    <p style="color: #34495e; margin: 0; line-height: 1.6; font-size: 15px;">
                        {ai_analysis.get('tips', texts.get('no_tips_available', 'No tips available'))}
                    </p>
                </div>
                
                <div style="background: linear-gradient(135deg, {suggestion_bg}, {suggestion_bg}dd); border: 2px solid {suggestion_color}; border-radius: 12px; padding: 16px; animation: suggestion-glow 2s ease-in-out infinite alternate;">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <span style="color: #2c3e50; font-weight: 700; font-size: 16px; display: flex; align-items: center;">
                            🎯 {texts.get('review_suggestion', 'Review Suggestion')}:
                        </span>
                        <span style="background: linear-gradient(135deg, {suggestion_color}, {suggestion_color}dd); color: white; padding: 10px 18px; border-radius: 20px; font-weight: bold; font-size: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.2); animation: suggestion-bounce 0.6s ease-out 0.5s both;">
                            {suggestion_icon} {texts.get('suggestions', {}).get(suggestion, suggestion)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
            @keyframes slideInUp {{
                0% {{ transform: translateY(30px); opacity: 0; }}
                100% {{ transform: translateY(0); opacity: 1; }}
            }}
            
            @keyframes pulse-border {{
                0%, 100% {{ box-shadow: 0 8px 32px rgba(0,0,0,0.1); }}
                50% {{ box-shadow: 0 8px 32px rgba(0,0,0,0.15), 0 0 0 3px {score_color}33; }}
            }}
            
            @keyframes success-ripple {{
                0% {{ transform: scale(0); opacity: 0.8; }}
                100% {{ transform: scale(1); opacity: 0; }}
            }}
            
            @keyframes score-pop {{
                0% {{ transform: scale(0.8) rotateZ(-5deg); opacity: 0; }}
                50% {{ transform: scale(1.1) rotateZ(2deg); }}
                100% {{ transform: scale(1) rotateZ(0deg); opacity: 1; }}
            }}
            
            @keyframes suggestion-glow {{
                0% {{ box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                100% {{ box-shadow: 0 4px 20px {suggestion_color}33; }}
            }}
            
            @keyframes suggestion-bounce {{
                0% {{ transform: scale(0.9) translateY(5px); opacity: 0; }}
                50% {{ transform: scale(1.05) translateY(-2px); }}
                100% {{ transform: scale(1) translateY(0); opacity: 1; }}
            }}
        </style>
    </div>
    """
    
    # Nettoyer les caches pour éviter l'accumulation
    if len(ai_analysis_cache) > 10:
        # Garder seulement les 5 plus récents
        keys_to_remove = list(ai_analysis_cache.keys())[:-5]
        for key in keys_to_remove:
            ai_analysis_cache.pop(key, None)
            is_analyzing.pop(key, None)
            analysis_results.pop(key, None)
    
    return enhanced_output

# import the necessary hooks
from aqt import gui_hooks, mw
from aqt.utils import showInfo, showWarning
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Tuple, Optional

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

# Langues supportées et leurs textes
LANGUAGES = {
    "english": {
        "name": "English",
        "ai_analysis": "AI Analysis",
        "improvement_tips": "Improvement Tips",
        "review_suggestion": "Review Suggestion",
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
        "models": ["deepseek/deepseek-r1:free", "openai/gpt-oss-20b:free", "qwen/qwen3-coder:free" ,"google/gemma-3n-e2b-it:free" ,"tencent/hunyuan-a13b-instruct:free"],
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
            "max_tokens": 200,  # Sera ajouté plus tard
            "messages": user_messages
        }
        
        if system_msg:
            formatted_data["system"] = system_msg
            
        return formatted_data
    
    else:
        # Format OpenAI (compatible avec OpenAI, DeepSeek, Groq)
        return {
            "messages": messages,
            "max_tokens": 200,  # Sera ajouté plus tard
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
                print(f'---Content-----{response_data['choices'][0]['message']['content']}')
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

def get_language_specific_prompt(language, true_answer, user_answer):
    """Génère un prompt selon la langue configurée"""
    
    prompts = {
        "english": f"""
        Analyze the student's answer compared to the expected answer and provide a structured evaluation.

        Expected answer: "{true_answer}"
        Student's answer: "{user_answer}"

        Please provide your evaluation in the following JSON format:
        {{
            "score": [number from 0 to 10],
            "tips": "[constructive feedback in English, maximum 100 words]",
            "review_suggestion": "[choose from: Again, Hard, Good, Easy]"
        }}

        Evaluation criteria:
        - Score 0-3: Incorrect or very incomplete answer → "Again"
        - Score 4-5: Partially correct but with significant errors → "Hard"  
        - Score 6-8: Correct answer with minor imperfections → "Good"
        - Score 9-10: Excellent and complete answer → "Easy"
        """,
        
        "french": f"""
        Analysez la réponse de l'étudiant par rapport à la réponse attendue et fournissez une évaluation structurée.

        Réponse attendue: "{true_answer}"
        Réponse de l'étudiant: "{user_answer}"

        Veuillez fournir votre évaluation au format JSON suivant:
        {{
            "score": [nombre de 0 à 10],
            "tips": "[conseils constructifs en français, maximum 100 mots]",
            "review_suggestion": "[choisir parmi: Again, Hard, Good, Easy]"
        }}

        Critères d'évaluation:
        - Score 0-3: Réponse incorrecte ou très incomplète → "Again"
        - Score 4-5: Réponse partiellement correcte mais avec des erreurs importantes → "Hard"  
        - Score 6-8: Réponse correcte avec quelques imperfections mineures → "Good"
        - Score 9-10: Réponse excellente et complète → "Easy"
        """,
        
        "spanish": f"""
        Analiza la respuesta del estudiante comparada con la respuesta esperada y proporciona una evaluación estructurada.

        Respuesta esperada: "{true_answer}"
        Respuesta del estudiante: "{user_answer}"

        Por favor proporciona tu evaluación en el siguiente formato JSON:
        {{
            "score": [número del 0 al 10],
            "tips": "[comentarios constructivos en español, máximo 100 palabras]",
            "review_suggestion": "[elegir entre: Again, Hard, Good, Easy]"
        }}

        Criterios de evaluación:
        - Puntuación 0-3: Respuesta incorrecta o muy incompleta → "Again"
        - Puntuación 4-5: Respuesta parcialmente correcta pero con errores significativos → "Hard"
        - Puntuación 6-8: Respuesta correcta con imperfecciones menores → "Good"
        - Puntuación 9-10: Respuesta excelente y completa → "Easy"
        """,
        
        "german": f"""
        Analysieren Sie die Antwort des Studenten im Vergleich zur erwarteten Antwort und geben Sie eine strukturierte Bewertung ab.

        Erwartete Antwort: "{true_answer}"
        Antwort des Studenten: "{user_answer}"

        Bitte geben Sie Ihre Bewertung im folgenden JSON-Format an:
        {{
            "score": [Zahl von 0 bis 10],
            "tips": "[konstruktives Feedback auf Deutsch, maximal 100 Wörter]",
            "review_suggestion": "[wählen Sie aus: Again, Hard, Good, Easy]"
        }}

        Bewertungskriterien:
        - Punktzahl 0-3: Falsche oder sehr unvollständige Antwort → "Again"
        - Punktzahl 4-5: Teilweise richtige Antwort, aber mit erheblichen Fehlern → "Hard"
        - Punktzahl 6-8: Richtige Antwort mit kleineren Unvollkommenheiten → "Good"
        - Punktzahl 9-10: Ausgezeichnete und vollständige Antwort → "Easy"
        """
    }
    
    return prompts.get(language, prompts["english"])

def analyze_answer_with_ai(true_answer: str, user_answer: str) -> dict:
    """
    Analyse la réponse de l'utilisateur avec l'IA
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
    
    # Utiliser le prompt selon la langue configurée
    prompt = get_language_specific_prompt(language, true_answer, user_answer)
    
    # Message système selon la langue
    system_messages = {
        "english": "You are an educational assistant that evaluates student responses constructively and kindly.",
        "french": "Vous êtes un assistant pédagogique qui évalue les réponses des étudiants de manière constructive et bienveillante.",
        "spanish": "Eres un asistente educativo que evalúa las respuestas de los estudiantes de manera constructiva y amable.",
        "german": "Sie sind ein pädagogischer Assistent, der die Antworten der Studenten konstruktiv und freundlich bewertet."
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
        
        return {"score": score, "tips": ai_response[:150] + "...", "review_suggestion": review_suggestion}
        
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