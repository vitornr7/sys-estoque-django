from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from datetime import datetime
from django.utils import formats, timezone
from django.db.models import Sum, F, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import csv

from .models import Estoque, Empresa, Produto
from .utilidades import paginar, filtrar_valor
from .forms import ProdutoForm, EstoqueForm, EstoqueAtualizarForm


@login_required
def listar_produtos(request):
    produtos = Produto.objects.all().order_by('nome')

    page = request.GET.get('page', 1)
    query = request.GET.get('q')
    valor1 = request.GET.get('valor1')
    valor2 = request.GET.get('valor2')
    opcao_valor = request.GET.get('opcao_valor')

    if query:
        produtos = Produto.objects.filter(Q(nome__icontains=query) | Q(
            codigo__icontains=query)).order_by('nome')
    if produtos:
        produtos = filtrar_valor(produtos, opcao_valor, valor1, valor2)

    produtos = paginar(produtos, page, 3)

    return render(request, 'estoque/listar_produtos.html', {'produtos': produtos})


@login_required
def atualizar_produto(request, pk):
    if request.user.is_superuser:
        produto = get_object_or_404(Produto, pk=pk)

        form = ProdutoForm(instance=produto)

        if request.method == "POST":
            form = ProdutoForm(data=request.POST, instance=produto)

            if form.is_valid():
                form.save()

                return HttpResponseRedirect(reverse('estoque:detalhes_produto', kwargs={'pk': produto.pk}))

        return render(request, 'estoque/alterar_produto.html', {'form': form, 'produto': produto})

    return render(request, 'estoque/alterar_produto.html')


@login_required
def atualizar_estoque(request, pk):
    usuario = get_object_or_404(Empresa, usuario=request.user)
    produto = get_object_or_404(Produto, pk=pk)

    try:
        estoque = Estoque.objects.get(Q(empresa=usuario) & Q(produto=produto))
    except Estoque.DoesNotExist:
        return HttpResponseRedirect(reverse('estoque:detalhes_produto', kwargs={'pk': produto.pk}))

    form = EstoqueAtualizarForm(instance=estoque)

    if request.method == "POST":
        form = EstoqueAtualizarForm(data=request.POST, instance=estoque)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse('estoque:detalhes_produto', kwargs={'pk': produto.pk}))

    return render(request, 'estoque/alterar_estoque.html', {'form': form, 'produto': produto})


@login_required
def cadastrar_produto(request):
    if request.user.is_superuser:
        if request.method == "POST":
            empresa = get_object_or_404(Empresa, usuario=request.user)
            produto_form = ProdutoForm(data=request.POST)
            estoque_form = EstoqueForm(data=request.POST)

            if produto_form.is_valid() and estoque_form.is_valid():
                produto = produto_form.save()

                estoque = estoque_form.save(commit=False)
                estoque.empresa = empresa
                estoque.produto = produto
                estoque.save()

                return HttpResponseRedirect(reverse('estoque:detalhes_produto', kwargs={'pk': produto.pk}))
        else:
            produto_form = ProdutoForm()
            estoque_form = EstoqueForm()

        return render(request, 'estoque/cadastro_produto.html', {'produto_form': produto_form, 'estoque_form': estoque_form})

    return render(request, 'estoque/cadastro_produto.html')


@login_required
def detalhes_produto(request, pk):
    usuario = get_object_or_404(Empresa, usuario=request.user)

    produto = get_object_or_404(Produto, pk=pk)
    try:
        estoque = Estoque.objects.get(Q(empresa=usuario) & Q(produto=produto))
    except Estoque.DoesNotExist:
        estoque = None

    return render(request, 'estoque/detalhes_produto.html', {'produto': produto, 'estoque': estoque})


@login_required
def avisos(request):
    page1 = request.GET.get('bpage', 1)
    page2 = request.GET.get('apage', 1)

    usuario = get_object_or_404(Empresa, usuario=request.user)
    baixo = Estoque.objects.filter(Q(empresa=usuario) & Q(quantidade__lte=F('baixo_estoque')))
    alto = Estoque.objects.filter(Q(empresa=usuario) & Q(quantidade__gte=F('alto_estoque')))

    baixo = paginar(baixo, page1, 3)
    alto = paginar(alto, page2, 3)

    return render(request, 'estoque/avisos.html', {'baixo': baixo, 'alto': alto})
