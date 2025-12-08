from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Currency, PaymentGateway, SiteSettings
from .serializers import CurrencySerializer, PaymentGatewaySerializer, SiteSettingsSerializer


class SiteSettingsView(generics.RetrieveAPIView):
    """Get site settings (public endpoint)"""
    permission_classes = [permissions.AllowAny]
    serializer_class = SiteSettingsSerializer
    
    def get_object(self):
        return SiteSettings.get_settings()


class CurrencyListView(generics.ListAPIView):
    """List all active currencies"""
    permission_classes = [permissions.AllowAny]
    serializer_class = CurrencySerializer
    queryset = Currency.objects.filter(is_active=True)


class PaymentGatewayListView(generics.ListAPIView):
    """List all active payment gateways"""
    permission_classes = [permissions.AllowAny]
    serializer_class = PaymentGatewaySerializer
    queryset = PaymentGateway.objects.filter(is_active=True).prefetch_related('supported_currencies')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def convert_currency(request):
    """Convert amount between currencies"""
    from_currency_code = request.data.get('from_currency')
    to_currency_code = request.data.get('to_currency')
    amount = request.data.get('amount', 0)
    
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return Response({'error': 'Invalid amount'}, status=400)
    
    try:
        from_currency = Currency.objects.get(code=from_currency_code, is_active=True)
        to_currency = Currency.objects.get(code=to_currency_code, is_active=True)
    except Currency.DoesNotExist:
        return Response({'error': 'Currency not found'}, status=404)
    
    # Convert to base currency first
    base_amount = amount / from_currency.exchange_rate
    # Then convert to target currency
    converted_amount = base_amount * to_currency.exchange_rate
    
    return Response({
        'from_currency': from_currency_code,
        'to_currency': to_currency_code,
        'amount': amount,
        'converted_amount': round(converted_amount, to_currency.decimal_places),
        'formatted': to_currency.format_price(converted_amount)
    })
