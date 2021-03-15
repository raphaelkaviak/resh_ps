from users.models import MyUser
from rest_framework import viewsets, serializers
from rest_framework import permissions
from users.serializers import RegisterSerializer, LoginSerializer, ChangePasswordSerializer, UserChangeSerializer
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import viewsets
from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import login, logout, authenticate
from django.views.generic import TemplateView, UpdateView, DeleteView
from users.forms import RegisterAPIRenderer
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from users.backends import EmailOrUsernameModelBackend

from rest_framework.exceptions import APIException
from django.utils.encoding import force_text
from rest_framework import status

from django.core import serializers as core_serializers


class HomePageView(TemplateView, APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    template_name = "home.html"

class RegisterView(APIView):
    model = MyUser
    serializer_class = RegisterSerializer
    renderer_classes = [TemplateHTMLRenderer]
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    template_name = "register.html"

    def get(self, request):
        serializer = RegisterSerializer()
        return render(request, "register.html", {"serializer": serializer})

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if(serializer.is_valid()):
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            if MyUser.objects.filter(email=email).exists() or MyUser.objects.filter(username=username).exists():
                return redirect("pages:register")
            if serializer.validated_data['password'] == serializer.validated_data['password2']:
                serializer.validated_data.pop("password2")
                new_user = serializer.create(serializer.validated_data)
                new_user.set_password(serializer.validated_data['password'])
                new_user.save()
                login(request, new_user)
                return redirect("pages:home")
            else:
                return redirect("pages:register")
        return render(request, "register.html", {"serializer": serializer})

class MyUserLoginView(APIView):
    model = MyUser
    serializer_class = LoginSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = (AllowAny,)
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "login.html"

    def get(self, request):
        serializer = LoginSerializer()
        return render(request, "login.html", {"serializer": serializer})

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if(serializer.is_valid()):
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = EmailOrUsernameModelBackend.authenticate(self, request, username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                return redirect("pages:home")
                # return Response(status=status.HTTP_200_OK)
            else:
                return redirect("pages:login")
        return render(request, "login.html", {"serializer": serializer})

class LogoutPageView(LogoutView):
    pass

class ChangePasswordView(APIView):
    model = MyUser
    serializer_class = ChangePasswordSerializer
    renderer_classes = [TemplateHTMLRenderer]
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    template_name = "change_password.html"
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = ChangePasswordSerializer()
        return render(request, "change_password.html", {"serializer": serializer})

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = MyUser.objects.get(username=request.user)
            if not user.check_password(serializer.validated_data.get("old_password")):
                return redirect("pages:change_password")
            
            user.set_password(serializer.validated_data.get("new_password"))
            user.save()
            login(request, user)
            return render(request, 'senha_alterada.html', {})

    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = MyUser.objects.get(username=request.user)
            if not user.check_password(serializer.validated_data.get("old_password")):
                return redirect("pages:change_password")
            
            user.set_password(serializer.validated_data.get("new_password"))
            user.save()
            content = {'Mensagem': 'Parabéns! Você alterou sua senha com sucesso!'}
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(APIView):
    model = MyUser
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = MyUser.objects.get(username=request.user)
        user.is_active = False
        user.save()
        logout(request)

        return redirect("pages:login")

    def delete(self, request):
        try :
            request.user.delete()
            print("tou no try")
            return Response(status=status.HTTP_200_OK)
        except:
            print("tou no except")
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ChangeUserInfoView(generics.UpdateAPIView, APIView):
    model = MyUser
    authentication_classes = [TokenAuthentication, SessionAuthentication, BasicAuthentication]
    permission_classes = (IsAuthenticated,)
    serializer_class = UserChangeSerializer
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "success.html"

    def get(self, request):
        serializer = UserChangeSerializer()
        return render(request, "change_info.html", {"serializer": serializer})

    def post(self, request):
        serializer = UserChangeSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            if (MyUser.objects.filter(email=email).exists() and MyUser.objects.get(email=email).email != request.user.email) or (MyUser.objects.filter(username=username).exists() and MyUser.objects.get(username=username) != request.user):
                return redirect("pages:change_info")
            user = MyUser.objects.get(username=request.user)
            updated_user = serializer.update(user, serializer.validated_data)
            updated_user.save()
        else:
            redirect("pages:login")

        return redirect("pages:home")

    def put(self, request):
        serializer = UserChangeSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            email = serializer.validated_data['email']
            if (MyUser.objects.filter(email=email).exists() and MyUser.objects.get(email=email).email != request.user.email) or (MyUser.objects.filter(username=username).exists() and MyUser.objects.get(username=username) != request.user):
                content = {"mensagem":"Nome de usuário ou email já em uso"}
                return Response(content, status=status.HTTP_403_FORBIDDEN)
            user = MyUser.objects.get(username=request.user)
            updated_user = serializer.update(user, serializer.validated_data)
            updated_user.save()
            content = {"mensagem":"Dados atualizados com sucesso"}
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
           return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)

