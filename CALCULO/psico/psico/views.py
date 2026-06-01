from django.shortcuts import render

def home(request):
    return render(request, 'index/home.html')

def chat(request):                                    # ← agrega esto
    return render(request, 'index/chat.html')