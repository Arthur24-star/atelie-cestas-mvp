# Ateliê de Cestas e Presentes Personalizados

## Sobre o projeto

Este projeto tem como objetivo desenvolver um MVP para auxiliar na organização de pedidos de um ateliê de cestas e presentes personalizados.

## Objetivo

Facilitar a seleção de produtos, o preenchimento dos dados do cliente, o agendamento da entrega e a visualização do resumo do pedido.

## Funcionalidades planejadas

- Catálogo de insumos e seleção de itens.
- Atualização do subtotal do pedido.
- Cadastro dos dados do cliente.
- Agendamento da data de entrega.
- Resumo do pedido e opção de confirmação via WhatsApp.

## Tecnologias

As tecnologias serão definidas de acordo com a implementação do MVP.

## Contexto acadêmico

Projeto desenvolvido como parte da disciplina Projeto de Software, no curso de Análise e Desenvolvimento de Sistemas (ADS).

## Status

Em desenvolvimento.


## Revisão técnica e decisões de implementação

O fluxo de criação de pedidos foi revisado considerando validação de dados, consistência dos valores e persistência no banco de dados.

- **Validação de entrada:** o sistema verifica o nome do cliente, o WhatsApp, a seleção de produtos e a data de entrega.
- **Integridade dos produtos:** os itens selecionados são filtrados para considerar apenas identificadores existentes no catálogo.
- **Cálculo do pedido:** o total é calculado a partir dos preços definidos no catálogo, com arredondamento para duas casas decimais.
- **Persistência:** após a validação, o pedido é registrado no banco de dados e seu identificador é recuperado para exibição da confirmação.
- **Experiência do usuário:** mensagens de validação orientam o preenchimento correto do formulário.

Esta revisão documenta as decisões técnicas existentes no MVP e serve como base para futuras melhorias e testes automatizados.
