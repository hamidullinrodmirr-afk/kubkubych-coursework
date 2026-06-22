from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsAdmin
from .services import low_stock_report, products_report, sales_report, users_report


class SalesAnalyticsView(APIView):
    """GET /api/analytics/sales/ — продажи и выручка."""

    permission_classes = (IsAdmin,)

    def get(self, request):
        return Response(sales_report())


class ProductsAnalyticsView(APIView):
    """GET /api/analytics/products/ — популярность наборов."""

    permission_classes = (IsAdmin,)

    def get(self, request):
        return Response(products_report())


class UsersAnalyticsView(APIView):
    """GET /api/analytics/users/ — активность пользователей."""

    permission_classes = (IsAdmin,)

    def get(self, request):
        return Response(users_report())


class LowStockAnalyticsView(APIView):
    """GET /api/analytics/low-stock/ — наборы с низким остатком."""

    permission_classes = (IsAdmin,)

    def get(self, request):
        return Response(low_stock_report())
