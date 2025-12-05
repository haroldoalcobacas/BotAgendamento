from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics
from django.utils.dateparse import parse_date, parse_time
from datetime import datetime, timedelta

# Importações dos Modelos e Serializers
from .models import Booking, Customer, Resource
from .serializers import BookingSerializer

# Importações dos Serviços
from .services.nlp_v2 import interpretar_mensagem
from .services.whatsapp import enviar_whatsapp


def index(request):
    """View simples para testar a aplicação web, se necessário."""
    return render(request, "index.html", {})


@api_view(["POST"])
def whatsapp_webhook(request):
    """
    Recebe o webhook do gateway do WhatsApp, interpreta a mensagem 
    e executa a lógica de reserva no banco de dados.
    """
    data = request.data
    msg = data.get("body") or data.get("text") or ""
    # Assume que 'phone' é o número do remetente no formato +55XXXXXXXXXXXX
    phone = data.get("from") or data.get("sender") or data.get("author") 

    if not phone:
        return Response({"error": "phone not provided"}, status=400)

    # 1. Preparação: Cliente e Interpretação
    customer, _ = Customer.objects.get_or_create(phone=phone)
    parsed = interpretar_mensagem(msg)

    intent = parsed.get("intent")
    date_str = parsed.get("date")       # Ex: 2025-12-31
    time_str = parsed.get("time")       # Ex: 14:00
    resource_name = parsed.get("resource_name") # Ex: "Sala A"
    duration = parsed.get("duration_minutes")
    
    # Duração padrão: 60 minutos (1 hora)
    duration_minutes = duration if duration is not None and duration > 0 else 60

    # --------------------
    # 2. Criar reserva (criar_reserva, reservar)
    # --------------------
    if intent in ["criar_reserva", "reservar"]:
        
        # 2a. Lógica de Recurso
        try:
            if resource_name:
                # Tenta encontrar o recurso pelo nome (case-insensitive)
                resource = Resource.objects.get(name__iexact=resource_name)
            else:
                # Se o usuário não especificou, tenta pegar o primeiro recurso como padrão
                resource = Resource.objects.first() 
                if not resource:
                    enviar_whatsapp(phone, "🚫 Não há salas cadastradas para reserva. Fale com um administrador.")
                    return Response({"status": "no_resources"})

        except Resource.DoesNotExist:
            enviar_whatsapp(phone, f"🚫 Não encontrei a sala '{resource_name}'. Por favor, verifique o nome e tente novamente.")
            return Response({"status": "resource_not_found"})
            
        # 2b. Checagem de Dados
        if not date_str or not time_str:
            enviar_whatsapp(phone, f"Para reservar a *{resource.name}*, especifique a **data e o horário** (Ex: 'reservar amanhã às 15:00').")
            return Response({"status": "missing_info"})
            
        try:
            d = parse_date(date_str)
            t = parse_time(time_str)
            start_dt = datetime.combine(d, t)
            end_dt = start_dt + timedelta(minutes=duration_minutes)
        except Exception:
            enviar_whatsapp(phone, "❌ Não consegui entender a data ou o horário. Tente novamente no formato dd/mm/aaaa hh:mm.")
            return Response({"status": "bad_date_time"})

        # 2c. Checar conflito no banco (Filtra por Recurso)
        conflict = Booking.objects.filter(
            resource=resource, # Filtra a ocupação por sala!
            date=d,
            start_time__lt=end_dt.time(),
            end_time__gt=start_dt.time(),
            status="confirmed"
        ).exists()

        if conflict:
            msg_busy = f"🚫 Desculpe, a sala **{resource.name}** está reservada das {start_dt.strftime('%H:%M')} às {end_dt.strftime('%H:%M')} em {d.strftime('%d/%m')}. Consulte a disponibilidade."
            enviar_whatsapp(phone, msg_busy)
            return Response({"status": "busy"})

        # 2d. Criar reserva
        booking = Booking.objects.create(
            customer=customer,
            resource=resource, # Associa o Recurso
            date=d,
            start_time=start_dt.time(),
            end_time=end_dt.time(),
            status="confirmed"
        )
        
        # Envio de confirmação
        msg_confirma = f"✅ Reserva **Confirmada** na sala **{resource.name}** para {d.strftime('%d/%m')}:\nHorário: *{start_dt.strftime('%H:%M')} às {end_dt.strftime('%H:%M')}* ({duration_minutes} minutos).\nObrigado por reservar!"
        enviar_whatsapp(phone, msg_confirma)
        
        return Response({"status": "confirmed", "booking_id": booking.id})

    # --------------------
    # 3. Cancelar reserva (cancelar_reserva, cancelar)
    # --------------------
    elif intent in ["cancelar_reserva", "cancelar"]:
        if not date_str or not time_str:
            enviar_whatsapp(phone, "Para cancelar, preciso da **data e horário** da reserva (Ex: 'cancelar dia 10 às 17h').")
            return Response({"status": "missing_info"})

        try:
            d = parse_date(date_str)
            t = parse_time(time_str)
        except Exception:
            enviar_whatsapp(phone, "❌ Data ou horário inválido para o cancelamento.")
            return Response({"status": "bad_date_time"})

        # Tenta encontrar e cancelar a reserva
        try:
            # Busca a reserva pelo cliente, data, horário e status confirmado
            booking = Booking.objects.get(
                customer=customer,
                date=d,
                start_time=t,
                status="confirmed"
            )
            # Atualiza o status
            booking.status = "canceled"
            booking.save()
            enviar_whatsapp(phone, f"🗑️ Reserva cancelada com sucesso para {d.strftime('%d/%m')} às {t.strftime('%H:%M')}.")
            return Response({"status": "canceled"})
        except Booking.DoesNotExist:
            enviar_whatsapp(phone, "Não encontrei nenhuma reserva **ativa** para você nesta data e horário.")
            return Response({"status": "not_found"})

    # --------------------
    # 4. Consultar disponibilidade (consultar_disponibilidade, listar_disponibilidade)
    # --------------------
    elif intent in ["consultar_disponibilidade", "listar_disponibilidade"]:
        if not date_str:
            enviar_whatsapp(phone, "Para consultar a agenda, preciso da data (Ex: 'horários disponíveis amanhã').")
            return Response({"status": "missing_date"})
        
        try:
            d = parse_date(date_str)
        except Exception:
            enviar_whatsapp(phone, "❌ Data inválida. Tente no formato dd/mm/aaaa.")
            return Response({"status": "bad_date"})

        # Filtra todas as reservas confirmadas para o dia
        bookings = Booking.objects.filter(date=d, status="confirmed").order_by('resource__name', 'start_time')
        
        if not bookings:
            msg = f"🎉 Ótima notícia! Não há reservas para {d.strftime('%d/%m')}. Todas as salas estão **totalmente disponíveis**!"
        else:
            # Agrupar por recurso para uma resposta mais clara
            busy_slots_by_resource = {}
            for b in bookings:
                resource_name = b.resource.name if b.resource else "N/A"
                if resource_name not in busy_slots_by_resource:
                    busy_slots_by_resource[resource_name] = []
                busy_slots_by_resource[resource_name].append(
                    f"{b.start_time.strftime('%H:%M')} - {b.end_time.strftime('%H:%M')}"
                )
            
            msg = f"🗓️ Horários Ocupados em {d.strftime('%d/%m')}:\n\n"
            for name, slots in busy_slots_by_resource.items():
                msg += f"**{name}**: {', '.join(slots)}\n"
            
            msg += "\n*Os demais horários e salas estão livres.*"
            
        enviar_whatsapp(phone, msg)
        return Response({"date": d.strftime("%Y-%m-%d"), "slots": busy_slots_by_resource})

    # --------------------
    # 5. Intent Desconhecida / Falha
    # --------------------
    else:
        enviar_whatsapp(phone, "🤖 Olá! Sou o bot de reservas do Estúdio. Posso agendar, cancelar ou consultar a disponibilidade.\n\n*Diga 'Reservar Sala A amanhã às 16h' ou 'Ver horários disponíveis hoje'.*")
        return Response({"status": "unknown_intent"})
    

# API REST padrão para listar/criar reservas
class BookingListCreate(generics.ListCreateAPIView):
    """API para administradores listarem e criarem reservas (via REST)"""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer