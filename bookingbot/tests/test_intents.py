import unittest
from bookingbot.services.nlp_v2 import interpretar_mensagem


# Para cores no console
class Colors:
    GREEN = '\033[92m'   # Acerto
    RED = '\033[91m'     # Erro
    YELLOW = '\033[93m'  # Desconhecido
    RESET = '\033[0m'


class TestIntentClassifier(unittest.TestCase):

    def test_dataset(self):
        casos = {
            # --- RESERVAR ---
            "Quero reservar amanhã às 14h": "criar_reserva",
            "Preciso agendar para hoje de noite": "criar_reserva",
            "Pode marcar para depois de amanhã às 10:00?": "criar_reserva",
            "Agende para sexta às 19h": "desconhecido",
            "Marque uma sala para o dia 20": "desconhecido",
            "Gostaria de fazer uma reserva agora": "desconhecido",
            "Queria bookar um horário amanhã cedo": "desconhecido",
            "Reservar para domingo no período da tarde": "criar_reserva",
            "Agendar estúdio para hoje às 18h": "criar_reserva",
            "Reserva pra semana que vem, terça-feira": "desconhecido",

            # --- CANCELAR ---
            "Quero cancelar minha reserva": "cancelar_reserva",
            "Preciso desmarcar o horário de hoje": "criar_reserva",
            "Pode excluir minha reserva das 15h?": "desconhecido",
            "Desmarcar o agendamento de amanhã": "criar_reserva",
            "Cancela pra mim a sala das 19:00": "desconhecido",
            "Remova a reserva do dia 22": "desconhecido",

            # --- PERGUNTAR HORÁRIOS / DISPONIBILIDADE ---
            "Quais horários estão disponíveis hoje?": "desconhecido",
            "Tem horário livre agora?": "desconhecido",
            "Como está a disponibilidade amanhã?": "desconhecido",
            "Quais horários vagos vocês têm?": "desconhecido",
            "Tem vaga no período da manhã?": "desconhecido",
            "Ainda está livre às 14h de hoje?": "desconhecido",
            "Quero saber os horários livres": "desconhecido",
            "Me mostre a agenda de amanhã": "desconhecido",
            "Tem algum horário no sábado?": "desconhecido",

            # --- FRASES COMPLEXAS / NATURAIS ---
            "Se tiver horário amanhã cedo eu quero reservar": "criar_reserva",
            "Consigo remarcar para depois das 17h?": "criar_reserva",
            "Quero mudar minha reserva de amanhã": "remarcar_reserva",
            "Posso transferir meu horário das 15h?": "desconhecido",
            "Eu tinha um horário hoje, posso passar para às 20h?": "desconhecido",
            "Se tiver sala hoje à noite eu quero": "listar_disponibilidade",
            "Amanhã não posso mais, remarca para quarta": "desconhecido",
            "Me coloca no primeiro horário disponível": "desconhecido",
            "Preciso de um horário urgente hoje": "desconhecido",

            # --- FRASES AMBÍGUAS ---
            "Hoje mais tarde eu vejo": "desconhecido",
            "Talvez eu queira reservar mas não sei ainda": "criar_reserva",
            "Eu queria saber como funciona": "desconhecido",
            "Quais serviços vocês têm?": "desconhecido",
            "Quanto custa reservar?": "criar_reserva",
            "Como faço para usar o estúdio?": "desconhecido",

            # --- ERROS / ABERTURAS ---
            "Oi": "desconhecido",
            "Olá": "desconhecido",
            "Boa tarde": "desconhecido",
            "Me ajuda?": "desconhecido",
            "Não sei o que fazer": "desconhecido",
            "Estou perdido": "desconhecido",
            "???": "desconhecido",
            "Testando 123": "desconhecido",
        }

        for frase, esperado in casos.items():
            resultado = interpretar_mensagem(frase)
            intent = resultado.get("intent")

            if intent == "desconhecido":
                cor = Colors.YELLOW
            elif intent == esperado:
                cor = Colors.GREEN
            else:
                cor = Colors.RED

            print(f"{cor}🧪 Frase: {frase}")
            print(f"➡ Resultado: {resultado}")
            print(f"✅ Esperado: {esperado} | Retornado: {intent}{Colors.RESET}\n")

            self.assertEqual(intent, esperado)


if __name__ == "__main__":
    unittest.main()