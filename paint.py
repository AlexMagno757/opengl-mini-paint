"""
Projeto: Mini Paint 2D (Motor de Rasterização)
Autor: Alexandre Magno e Alline Aparecida
Instituição: Universidade Federal de Uberlândia (UFU)
Data: Novembro / 2026

Descrição: 
Implementação de baixo nível de primitivas gráficas (Bresenham, Midpoint Circle, 
Flood Fill com Pilha) e manipulação direta de framebuffer utilizando Python, 
GLFW, PyOpenGL e NumPy.

"""


import glfw
from OpenGL.GL import *
from PIL import Image
import numpy as np
import math
import tkinter as tk
from tkinter import simpledialog

class MiniPaint:
    def __init__(self):

        #inicializacoes
        self.width = 800
        self.height = 650
        self.window = None
        self.framebuffer = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
        self.backup_framebuffer = None


        self.is_drawing = False
        self.current_color = (0, 0, 0)

        #mapa de cores
        self.color_map = {
            glfw.KEY_K: (0, 0, 0),       # Preto 
            glfw.KEY_W: (255, 255, 255), # Branco
            glfw.KEY_R: (255, 0, 0),     # Vermelho
            glfw.KEY_G: (0, 255, 0),     # Verde
            glfw.KEY_B: (0, 0, 255),     # Azul
            glfw.KEY_Y: (255, 255, 0),   # Amarelo
            glfw.KEY_C: (0, 255, 255),   # Ciano
            glfw.KEY_M: (255, 0, 255),   # Magenta 
        }

        #ferramentas
        self.current_tool = 'LAPIS'
        self.formas = ['RETANGULO', 'RETANGULO_CHEIO', 'CIRCULO', 'CIRCULO_CHEIO']

        #controle 
        self.brush_size = 1  # 1 = fino, 3 = médio, 5 = grosso
        self.saved_pencil_size = 1
        self.last_x = 0
        self.last_y = 0

    def init_glfw(self):
        if not glfw.init(): return False

        glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
        self.window = glfw.create_window(self.width, self.height, "Mini Paint ", None, None)
        
        if not self.window:
            glfw.terminate()
            return False
        
        glfw.make_context_current(self.window)
        glfw.set_mouse_button_callback(self.window, self.mouse_button_callback)
        glfw.set_cursor_pos_callback(self.window, self.cursor_pos_callback)
        glfw.set_key_callback(self.window, self.key_callback)
        return True

    def put_pixel(self, x, y, color):

        if y <= 50:
            return

        x, y = int(x), int(y)
        offset = self.brush_size // 2  

        #inverte pois o sistema de janelas do SO posiciona a origem no canto superior esquerdo e a renderização do glDrawPixels é o contrário
        y_matriz = self.height - 1 - y

        # Calcula os limites do quadrado para pintar os pixels e não sair da borda
        y_min = max(0, y_matriz - offset)
        y_max = min(self.height, y_matriz + offset + 1)
        x_min = max(0, x - offset)
        x_max = min(self.width, x + offset + 1)

        #verificação de borda
        if y_min < y_max and x_min < x_max:
            self.framebuffer[y_min:y_max, x_min:x_max] = color #eliminamos uso de for 


    #BRESEHAM
    def bresenham_line(self, x0, y0, x1, y1, color):

        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        err = dx - dy

        x, y = x0, y0

        while True:
            self.put_pixel(x, y, color)

            if x == x1 and y == y1:
                break

            e2 = 2 * err

            if e2 > -dy:
                err -= dy
                x += sx

            if e2 < dx:
                err += dx
                y += sy

    def get_pixel(self, x, y):
    
            x, y = int(x), int(y)
            y_matriz = self.height - 1 - y
    
            if 0 <= x < self.width and 0 <= y_matriz < self.height:
                return tuple(self.framebuffer[y_matriz][x])
            return None
    
    #pinta uma linha inteira (pra usar no retangulo e no circulo cheio)
    def draw_hline(self, x0, x1, y, color,clipping_ui:False):

            if clipping_ui and y<=50:
                return;
    
            y_matriz = self.height - 1 - y
            x_min = max(0, min(x0, x1))
            x_max = min(self.width, max(x0, x1) + 1) 
    
            if 0 <= y_matriz < self.height and x_min < x_max:   
                self.framebuffer[y_matriz, x_min:x_max] = color

    #RENTANGULO
    def draw_rect(self, x0, y0, x1, y1, color):
            self.bresenham_line(x0, y0, x1, y0, color)
            self.bresenham_line(x1, y0, x1, y1, color)
            self.bresenham_line(x1, y1, x0, y1, color)
            self.bresenham_line(x0, y1, x0, y0, color)

    #RETANGULO PREENCHIDO
    def draw_rect_filled(self, x0, y0, x1, y1, color,clipping_ui=False):
            for y in range(int(min(y0, y1)), int(max(y0, y1)) + 1):
                self.draw_hline(x0, x1, y, color, clipping_ui= clipping_ui);

    #CIRCULO
    def plota_octeto(self, xc, yc, x, y, color):
        self.put_pixel(xc + x, yc + y, color)
        self.put_pixel(xc - x, yc + y, color)
        self.put_pixel(xc + x, yc - y, color)
        self.put_pixel(xc - x, yc - y, color)
        self.put_pixel(xc + y, yc + x, color)
        self.put_pixel(xc - y, yc + x, color)
        self.put_pixel(xc + y, yc - x, color)
        self.put_pixel(xc - y, yc - x, color)

    #ALGORITMO MID POINT CIRCLE
    def mid_point_circle(self, xc, yc, r , color):

        xc,yc,r = int(xc), int(yc), int(r)

        x = 0
        y = r
        d = 1 - r

        self.plota_octeto(xc, yc, x, y, color)

        while (y > x):
            if (d < 0):
                d += (2 * x) + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1
            self.plota_octeto(xc, yc, x, y, color)

    #CIRCULO PREENCHIDO
    def plotaOctetoCheio(self, xc, yc, x, y, color):
            self.draw_hline(xc - x, xc + x, yc + y, color,True)
            self.draw_hline(xc - x, xc + x, yc - y, color,True)
            self.draw_hline(xc - y, xc + y, yc + x, color,True)
            self.draw_hline(xc - y, xc + y, yc - x, color,True)

    #MESMO ALGORITMO PARA PREENCHIDO (MID-POINT)
    def midpointCircleCheio(self, xc, yc, r, color):
            x = 0
            y = r
            d = 1 - r
    
            self.plotaOctetoCheio(xc, yc, x, y, color)
    
            while y > x:
                if d < 0:
                    d += (2 * x) + 3
                else:
                    d += 2 * (x - y) + 5
                    y -= 1
                x += 1
                self.plotaOctetoCheio(xc, yc, x, y, color)

    #PARA CHAMAR O DESENHO DAS FORMAS
    def desenha_forma(self, x, y):
            self.framebuffer[:] = self.backup_framebuffer
    
            x0, y0 = int(self.last_x), int(self.last_y)
            x1, y1 = int(x), int(y)
    
            if self.current_tool == 'RETANGULO':
                self.draw_rect(x0, y0, x1, y1, self.current_color)

            elif self.current_tool == 'RETANGULO_CHEIO':
                self.draw_rect_filled(x0, y0, x1, y1, self.current_color,True)

            elif self.current_tool in ['CIRCULO', 'CIRCULO_CHEIO']:
                dx = x1 - x0
                dy = y1 - y0
                raio = math.isqrt(dx*dx + dy*dy)

                if self.current_tool == 'CIRCULO':
                    self.mid_point_circle(x0, y0, raio, self.current_color)
                else:
                    self.midpointCircleCheio(x0, y0, raio, self.current_color)

    #PARA PREENCHER (BALDE DE TINTA)
    def flood_fill(self, x, y, nova_cor):
            x, y = int(x), int(y)
            cor_alvo = self.get_pixel(x, y)
    
            if cor_alvo is None or cor_alvo == nova_cor:
                return
    
            tamanho = self.brush_size   
            self.brush_size = 1  # o balde pinta pixel por pixel, entt a espessura tem que ser 1
    
            pilha = [(x, y)]
    
            while pilha:
                px, py = pilha.pop()
    
                if self.get_pixel(px, py) != cor_alvo:
                    continue
    
                self.put_pixel(px, py, nova_cor)
    
                pilha.append((px + 1, py))
                pilha.append((px - 1, py))
                pilha.append((px, py + 1))
                pilha.append((px, py - 1))
    
            self.brush_size = tamanho

    #SALVAR DESENHO
    def salvar_jpg(self, nome):

        if not nome.endswith(".jpg"):
            nome += ".jpg"

        #Inverte a matriz
        matriz_invertida = np.flipud(self.framebuffer)

        desenho = matriz_invertida[50:,:] #tirando a interface de cores
        
        # Converte a matriz NumPy para um objeto de Imagem RGB
        imagem = Image.fromarray(desenho, mode='RGB')
        imagem.save(nome, format="JPEG", quality=95)
        print(f"Imagem salva em {nome}")

    #TECLADO
    def key_callback(self, window, key, scancode, action, mods):
        if action == glfw.PRESS:

            if key == glfw.KEY_L:
                if self.current_tool == 'BORRACHA':
                    self.brush_size = self.saved_pencil_size
                self.current_tool = 'LAPIS'
                print("Ferramenta: Lápis")

            elif key == glfw.KEY_A:
                if(self.current_tool != 'BORRACHA'):
                    self.saved_pencil_size = self.brush_size

                self.current_tool = 'BORRACHA'
                self.brush_size = 15    
                print("Ferramenta: Borracha")

            elif key in self.color_map:
                self.current_color = self.color_map[key]
                print(f"Cor alterada: {self.current_color}")


            elif key == glfw.KEY_1:
                self.brush_size = 1
                print("Espessura: Fina")

            elif key == glfw.KEY_2:
                self.brush_size = 3
                print("Espessura: Média")

            elif key == glfw.KEY_3:
                self.brush_size = 5
                print("Espessura: Grossa")

            elif key == glfw.KEY_4:
                if self.current_tool == 'BORRACHA': self.brush_size = self.saved_pencil_size
                self.current_tool= 'LINHA'
                print("Ferramente: Linha")

            elif key == glfw.KEY_5:
                if self.current_tool == 'BORRACHA': self.brush_size = self.saved_pencil_size
                self.current_tool = 'RETANGULO'
                print("Ferramenta: Retângulo vazado")

            elif key == glfw.KEY_6:
                if self.current_tool == 'BORRACHA': self.brush_size = self.saved_pencil_size
                self.current_tool = 'RETANGULO_CHEIO'
                print("Ferramenta: Retângulo preenchido")
            
            elif key == glfw.KEY_7:
                if self.current_tool == 'BORRACHA': self.brush_size = self.saved_pencil_size
                self.current_tool = 'CIRCULO'
                print("Ferramenta: Círculo vazado")
                
            elif key == glfw.KEY_8:
                if self.current_tool == 'BORRACHA': self.brush_size = self.saved_pencil_size
                self.current_tool = 'CIRCULO_CHEIO'
                print("Ferramenta: Círculo preenchido")

            elif key == glfw.KEY_9:
                self.current_tool = 'BALDE'
                print("Ferramenta: Balde de tinta")

            elif key == glfw.KEY_S:
                root = tk.Tk()
                root.withdraw()
                nome = simpledialog.askstring("Salvar Desenho", "Digite o nome do arquivo:")
                root.destroy()

                if nome:
                    self.salvar_jpg(nome)
            
            elif key == glfw.KEY_N:
                self.framebuffer.fill(255)
                self.desenha_interface()
                print("Tela limpa!")

            elif key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(window, True)

    #CLIQUE E SOLTAR O MOUSE
    def mouse_button_callback(self, window, button, action, mods):
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                self.last_x, self.last_y = glfw.get_cursor_pos(window)

                if self.last_y <= 50:
                    indice_botao = int((self.last_x - 10) // 40)

                    if 0 <= indice_botao <= 7:
                        cores_paleta = [(0,0,0), (255,255,255), (255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255), (255,0,255)]
                        self.current_color = cores_paleta[indice_botao]
                        print(f"Cor da paleta alterada: {self.current_color}")
                    return

                self.is_drawing = True

                if self.current_tool in ['LAPIS', 'BORRACHA']:
                    if self.current_tool == 'BORRACHA':
                        cor_ativa = (255, 255, 255)
                    else:
                        cor_ativa = self.current_color
                        
                    self.put_pixel(self.last_x, self.last_y, cor_ativa)

                elif self.current_tool == 'LINHA':
                    self.backup_framebuffer = np.copy(self.framebuffer)

                elif self.current_tool in self.formas:
                    self.backup_framebuffer = np.copy(self.framebuffer)

                elif self.current_tool == 'BALDE':
                    self.flood_fill(self.last_x, self.last_y, self.current_color)

            elif action == glfw.RELEASE:

                if not self.is_drawing:
                    return
                
                self.is_drawing = False
                if self.current_tool ==  'LINHA':
                    x_final, y_final = glfw.get_cursor_pos(window)
                    self.bresenham_line(self.last_x, self.last_y, x_final, y_final, self.current_color)

                if self.current_tool in self.formas:
                    x_final, y_final = glfw.get_cursor_pos(window)
                    self.desenha_forma(x_final, y_final)

    #MEXER O MOUSE
    def cursor_pos_callback(self, window, xpos, ypos):
        if self.is_drawing: 
            if self.current_tool in ['LAPIS', 'BORRACHA']:

                if self.current_tool == 'BORRACHA':
                    cor_ativa = (255, 255, 255)
                else:
                    cor_ativa = self.current_color
                                    
                self.bresenham_line(self.last_x, self.last_y, xpos, ypos, cor_ativa)

                self.last_x, self.last_y = xpos, ypos
            
            elif self.current_tool == 'LINHA':
                # [:] Copia apenas os valores para dentro da matriz existente
                self.framebuffer[:] = self.backup_framebuffer
                self.bresenham_line(self.last_x, self.last_y, xpos, ypos, self.current_color)
            
            elif self.current_tool in self.formas:
                self.desenha_forma(xpos, ypos)

    #INTERFACE DE CORES 
    def desenha_interface(self):
        # fundo da barra
        self.draw_rect_filled(0, 0, self.width, 50, (200, 200, 200))
        
        cores_paleta = [
            (0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), 
            (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)
        ]
        
        # botão terá 30x30 pixels, com 10 de espaçamento
        for i, cor in enumerate(cores_paleta):
            x_inicio = 10 + (i * 40)
            self.draw_rect_filled(x_inicio, 10, x_inicio + 30, 40, cor)
                        
        # Tira uma foto da matriz com a interface desenhada para servir de fundo base
        self.backup_framebuffer = np.copy(self.framebuffer)

    #EXECUCAO
    def run(self):
        if not self.init_glfw(): return
        print("\n---------- FUNÇÕES ----------")
        print("\nPression:\n(1) Espessura fina\n(2) Espessura média\n(3) Espessura grossa")
        print("\nFerramentas:\n(L) Lápis\n(A) Borracha\n(4) Linha\n(5/6) Retângulo vazado/Preenchido\n(7/8) Círculo vazado/Preenchido\n(9) balde")
        print("(N) limpa a tela\n(S) salva em desenho.ppm")

        self.desenha_interface()

        while not glfw.window_should_close(self.window):
            glClear(GL_COLOR_BUFFER_BIT)
            glRasterPos2i(-1, -1)
            glDrawPixels(self.width, self.height, GL_RGB, GL_UNSIGNED_BYTE, self.framebuffer)
            glfw.swap_buffers(self.window)
            glfw.poll_events()
        glfw.terminate()

if __name__ == "__main__":
    app = MiniPaint()
    app.run()