_TEMPLATES = {
    "pt": """\
Olá {name},

Muito obrigado pela visita à earthcache {gc} e espero que tenha sido interessante sobre o ponto de vista geológico.
As respostas estão dentro do pretendido.

Cumprimentos,
Fábio""",
    "en": """\
Hello {name},

Thank you very much for your visit to earthcache {gc}, I hope it was interesting from a geological point of view.
Your answers are correct.

Best regards,
Fábio""",
    "de": """\
Hallo {name},

Vielen Dank für deinen Besuch bei Earthcache {gc}, ich hoffe, er war aus geologischer Sicht interessant.
Deine Antworten sind korrekt.

Mit freundlichen Grüßen,
Fábio""",
    "es": """\
Hola {name},

Muchas gracias por la visita a la earthcache {gc}, espero que haya sido interesante desde el punto de vista geológico.
Las respuestas son correctas.

Saludos,
Fábio""",
    "fr": """\
Bonjour {name},

Merci beaucoup pour votre visite à l'earthcache {gc}, j'espère qu'elle a été intéressante d'un point de vue géologique.
Les réponses sont correctes.

Cordialement,
Fábio""",
    "nl": """\
Hallo {name},

Hartelijk bedankt voor je bezoek aan earthcache {gc}, ik hoop dat het interessant was vanuit geologisch oogpunt.
De antwoorden zijn correct.

Met vriendelijke groeten,
Fábio""",
    "it": """\
Ciao {name},

Grazie mille per la visita all'earthcache {gc}, spero che sia stata interessante dal punto di vista geologico.
Le risposte sono corrette.

Cordiali saluti,
Fábio""",
    "pl": """\
Cześć {name},

Dziękuję bardzo za wizytę przy earthcache {gc}, mam nadzieję, że była interesująca z geologicznego punktu widzenia.
Odpowiedzi są prawidłowe.

Pozdrawiam,
Fábio""",
    "ro": """\
Bună ziua {name},

Vă mulțumesc mult pentru vizita la earthcache {gc}, sper că a fost interesantă din punct de vedere geologic.
Răspunsurile sunt corecte.

Cu stimă,
Fábio""",
    "ru": """\
Привет {name},

Большое спасибо за визит на earthcache {gc}, надеюсь, он был интересен с геологической точки зрения.
Ваши ответы верны.

С уважением,
Fábio""",
    "sv": """\
Hej {name},

Tack så mycket för besöket vid earthcache {gc}, jag hoppas att det var intressant ur ett geologiskt perspektiv.
Svaren är korrekta.

Med vänliga hälsningar,
Fábio""",
    "da": """\
Hej {name},

Mange tak for besøget ved earthcache {gc}, jeg håber det var interessant fra et geologisk synspunkt.
Svarene er korrekte.

Med venlig hilsen,
Fábio""",
    "fi": """\
Hei {name},

Paljon kiitoksia vierailusta earthcache {gc} -kohteessa, toivottavasti se oli mielenkiintoinen geologisesta näkökulmasta.
Vastaukset ovat oikein.

Ystävällisin terveisin,
Fábio""",
}

_DEFAULT = "pt"


def get_default_reply(message_text: str, name: str = "", gc: str = "") -> str:
    try:
        from langdetect import detect
        lang = detect(message_text) if message_text else _DEFAULT
        template = _TEMPLATES.get(lang, _TEMPLATES[_DEFAULT])
    except Exception:
        template = _TEMPLATES[_DEFAULT]
    return template.format(name=name, gc=gc)
