import pygame
import random
import time
import itertools
import os
import heapq
import csv
import ast
from sprite import *
from setting import *

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.shuffle_time = 0
        self.start_shuffle = False
        self.previous_choice = ""
        self.start_game = False
        self.start_timer = False
        self.elapsed_time = 0
        self.high_score = self.get_high_score()

        file_exists = os.path.isfile("game_steps.csv")
        self.csv_file = open("game_steps.csv", mode="a", newline="")
        self.csv_writer = csv.writer(self.csv_file)
        if not file_exists:
            self.csv_writer.writerow(["Step", "Grid", "Goal", "Move"])  # Tiêu đề cột
        self.step_count = 0  # Đếm số bước
        self.is_solving = False  # Cờ xác định có đang giải đố thủ công hay không
        self.is_machine_solving = False  # Cờ xác định có đang giải đố bằng Hocmay hay không

    def save_grid_to_csv(self, move=None):
        # Chỉ lưu các bước nếu không phải trong chế độ học máy
        if not self.is_solving or self.is_machine_solving:
            return

        self.step_count += 1

        # Chuẩn bị dữ liệu để lưu vào CSV
        flat_grid = list(itertools.chain(*self.tiles_grid))
        flat_goal = list(itertools.chain(*self.tiles_grid_completed))

        # Ghi bước mới vào file CSV
        if move:
            self.csv_writer.writerow([self.step_count, flat_grid, flat_goal, move])
        else:
            self.csv_writer.writerow([self.step_count, flat_grid, flat_goal])

        print(f"Step {self.step_count}: {flat_grid}, Move: {move}")

        # Thêm dòng trống sau khi giải xong
        if self.is_solving and self.solution_index == len(self.solution_steps):
            self.csv_writer.writerow([])  # Thêm dòng trống

    def create_game(self):
        grid = [[x + y * GAME_SIZE for x in range(1, GAME_SIZE + 1)] for y in range(GAME_SIZE)]
        grid[-1][-1] = 0
        return grid

    def shuffle(self):
        possible_moves = []
        row, col = None, None
        for r, tiles in enumerate(self.tiles):
            for c, tile in enumerate(tiles):
                if tile.text == "empty":
                    row, col = r, c
                    if tile.right():
                        possible_moves.append("right")
                    if tile.left():
                        possible_moves.append("left")
                    if tile.up():
                        possible_moves.append("up")
                    if tile.down():
                        possible_moves.append("down")
                    break
            if row is not None:
                break

        if self.previous_choice == "right":
            possible_moves.remove("left") if "left" in possible_moves else possible_moves
        elif self.previous_choice == "left":
            possible_moves.remove("right") if "right" in possible_moves else possible_moves
        elif self.previous_choice == "up":
            possible_moves.remove("down") if "down" in possible_moves else possible_moves
        elif self.previous_choice == "down":
            possible_moves.remove("up") if "up" in possible_moves else possible_moves

        choice = random.choice(possible_moves)
        self.previous_choice = choice
        if choice == "right":
            self.tiles_grid[row][col], self.tiles_grid[row][col + 1] = self.tiles_grid[row][col + 1], self.tiles_grid[row][col]
        elif choice == "left":
            self.tiles_grid[row][col], self.tiles_grid[row][col - 1] = self.tiles_grid[row][col - 1], self.tiles_grid[row][col]
        elif choice == "up":
            self.tiles_grid[row][col], self.tiles_grid[row - 1][col] = self.tiles_grid[row - 1][col], self.tiles_grid[row][col]
        elif choice == "down":
            self.tiles_grid[row][col], self.tiles_grid[row + 1][col] = self.tiles_grid[row + 1][col], self.tiles_grid[row][col]

    def draw_tiles(self):
        self.tiles = []
        for row, x in enumerate(self.tiles_grid):
            self.tiles.append([])
            for col, tile in enumerate(x):
                if tile != 0:
                    self.tiles[row].append(Tile(self, col, row, str(tile)))
                else:
                    self.tiles[row].append(Tile(self, col, row, "empty"))

    def new(self):
        self.all_sprites = pygame.sprite.Group()
        self.tiles_grid = self.create_game()
        self.tiles_grid_completed = self.create_game()
        self.elapsed_time = 0
        self.start_timer = False
        self.start_game = False
        self.buttons_list = [
            Button(700, 100, 200, 50, "Shuffle", WHITE, BLACK),
            Button(700, 170, 200, 50, "Reset", WHITE, BLACK),
            Button(700, 240, 200, 50, "Giai", WHITE, BLACK),
            Button(700, 320, 200, 50, "Hocmay", WHITE, BLACK)
        ]
        self.draw_tiles()

    def run(self):
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

    def update(self):
        # Xử lý quá trình xáo trộn
        if self.start_shuffle:
            self.shuffle()
            self.draw_tiles()
            self.shuffle_time += 1
            if self.shuffle_time > 120:
                self.start_shuffle = False
                self.start_game = True
                self.start_timer = True

        # Xử lý đếm thời gian sau khi xáo trộn xong
        if self.start_timer:
            self.elapsed_time += self.clock.get_time() / 4000  # Update thời gian đã trôi qua

        # Xử lý giải đố bằng chế độ thủ công
        if hasattr(self, 'solution_steps') and self.solution_index < len(self.solution_steps):
            self.tiles_grid = [list(row) for row in self.solution_steps[self.solution_index]]
            self.solution_index += 1
            self.draw_tiles()

            move = self.solution_moves[self.solution_index - 1] if self.solution_index - 1 < len(
                self.solution_moves) else None

            if self.is_solving and not self.is_machine_solving:
                self.save_grid_to_csv(move=move)

            pygame.time.wait(100)

            if self.solution_index == len(self.solution_steps):
                self.is_solving = False  # Quá trình giải đố thủ công hoàn thành
                self.start_timer = False  # Stop the timer when puzzle is solved manually

        # Xử lý giải đố bằng học máy (từ CSV)
        if self.is_machine_solving and self.solution_index < len(self.solution_moves):
            move = self.solution_moves[self.solution_index]
            empty_row, empty_col = \
            [(r, c) for r, row in enumerate(self.tiles_grid) for c, val in enumerate(row) if val == 0][0]

            if move == "right" and empty_col > 0:
                self.tiles_grid[empty_row][empty_col], self.tiles_grid[empty_row][empty_col - 1] = \
                    self.tiles_grid[empty_row][empty_col - 1], self.tiles_grid[empty_row][empty_col]
            elif move == "left" and empty_col < GAME_SIZE - 1:
                self.tiles_grid[empty_row][empty_col], self.tiles_grid[empty_row][empty_col + 1] = \
                    self.tiles_grid[empty_row][empty_col + 1], self.tiles_grid[empty_row][empty_col]
            elif move == "up" and empty_row < GAME_SIZE - 1:
                self.tiles_grid[empty_row][empty_col], self.tiles_grid[empty_row + 1][empty_col] = \
                    self.tiles_grid[empty_row + 1][empty_col], self.tiles_grid[empty_row][empty_col]
            elif move == "down" and empty_row > 0:
                self.tiles_grid[empty_row][empty_col], self.tiles_grid[empty_row - 1][empty_col] = \
                    self.tiles_grid[empty_row - 1][empty_col], self.tiles_grid[empty_row][empty_col]

            self.solution_index += 1
            self.draw_tiles()

            pygame.time.wait(500)

            if self.solution_index == len(self.solution_moves):
                self.is_machine_solving = False  # Kết thúc chế độ học máy
                self.start_timer = False  # Stop the timer when machine solving is complete

        self.all_sprites.update()

    def draw_grid(self):
        for row in range(0, GAME_SIZE * TILESIZE, TILESIZE):
            pygame.draw.line(self.screen, LIGHTGREY, (row, 0), (row, GAME_SIZE * TILESIZE))
        for col in range(0, GAME_SIZE * TILESIZE, TILESIZE):
            pygame.draw.line(self.screen, LIGHTGREY, (0, col), (GAME_SIZE * TILESIZE, col))

    def draw(self):
        self.screen.fill(BGCOLOUR)
        self.all_sprites.draw(self.screen)
        self.draw_grid()
        for button in self.buttons_list:
            button.draw(self.screen)
        UIElement(750, 35, f"{self.elapsed_time:.3f}").draw(self.screen)
        UIElement(640, 300, f"High Score - {self.high_score:.3f}").draw(self.screen)
        pygame.display.flip()

    def solve_puzzle(self):
        self.is_solving = True  # Đảm bảo cờ này được bật khi bắt đầu giải đố
        self.initial_grid = [row[:] for row in self.tiles_grid]  # Lưu trạng thái ban đầu của bảng
        self.is_solving = True  # Đảm bảo cờ này được bật khi bắt đầu giải đố

        def heuristic(current, goal):
            dist = 0
            for r in range(GAME_SIZE):
                for c in range(GAME_SIZE):
                    value = current[r][c]
                    if value == 0:
                        continue
                    goal_r, goal_c = divmod(value - 1, GAME_SIZE)
                    dist += abs(r - goal_r) + abs(c - goal_c)
            return dist

        start = tuple(tuple(row) for row in self.tiles_grid)
        goal = tuple(tuple(row) for row in self.tiles_grid_completed)
        frontier = [(0, start)]
        came_from = {start: None}
        cost_so_far = {start: 0}
        move_from = {start: None}

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal:
                break

            empty_pos = [(r, c) for r, row in enumerate(current) for c, val in enumerate(row) if val == 0][0]
            r, c = empty_pos
            neighbors = []
            if c < GAME_SIZE - 1:
                neighbors.append((r, c + 1))
            if c > 0:
                neighbors.append((r, c - 1))
            if r < GAME_SIZE - 1:
                neighbors.append((r + 1, c))
            if r > 0:
                neighbors.append((r - 1, c))

            for nr, nc in neighbors:
                new_grid = [list(row) for row in current]
                new_grid[r][c], new_grid[nr][nc] = new_grid[nr][nc], new_grid[r][c]
                new_grid = tuple(tuple(row) for row in new_grid)
                if new_grid not in cost_so_far:
                    priority = cost_so_far[current] + 1 + heuristic(new_grid, goal)
                    heapq.heappush(frontier, (priority, new_grid))
                    came_from[new_grid] = current
                    cost_so_far[new_grid] = cost_so_far[current] + 1
                    move_from[new_grid] = (r, c, nr, nc)

        solution_steps = []
        solution_moves = []
        current = goal
        while current != start:
            solution_steps.append(current)
            r1, c1, r2, c2 = move_from[current]
            if r2 == r1 + 1:
                direction = "up"
            elif r2 == r1 - 1:
                direction = "down"
            elif c2 == c1 + 1:
                direction = "left"
            elif c2 == c1 - 1:
                direction = "right"
            else:
                direction = None
            solution_moves.append(direction)
            current = came_from[current]

        self.solution_steps = solution_steps[::-1]
        self.solution_moves = solution_moves[::-1]
        self.solution_index = 0

    def quit(self):
        self.csv_file.close()
        pygame.quit()

    def get_high_score(self):
        return 100  # Giả lập lấy high score từ một nguồn nào đó

    def save_score(self):
        with open("highscore.txt", "w") as file:
            file.write(str(self.high_score))

    def load_solution_from_csv(self):
        try:
            with open("game_steps.csv", mode="r") as file:
                csv_reader = csv.reader(file)
                next(csv_reader)  # Bỏ qua tiêu đề cột
                all_solutions = []  # Lưu tất cả các giải pháp
                current_solution = []
                for row in csv_reader:
                    if len(row) >= 4:  # Kiểm tra nếu dòng có ít nhất 4 cột
                        move = row[3]  # Cột chứa nước đi nằm ở vị trí thứ 4
                        current_solution.append(move)
                    else:
                        # Nếu gặp dòng trống hoặc dòng không đủ dữ liệu, kết thúc giải pháp hiện tại
                        if current_solution:
                            all_solutions.append(current_solution)
                        current_solution = []  # Bắt đầu giải pháp mới

                if current_solution:
                    all_solutions.append(current_solution)  # Lưu giải pháp cuối cùng nếu có

            if not all_solutions:
                print("No valid solutions found in CSV.")
                return None

            # Thử từng giải pháp để xem giải pháp nào dẫn đến kết quả đúng
            for solution_moves in all_solutions:
                temp_grid = [list(row) for row in self.tiles_grid]  # Bắt đầu từ lưới hiện tại
                for move in solution_moves:
                    empty_row, empty_col = \
                    [(r, c) for r, row in enumerate(temp_grid) for c, val in enumerate(row) if val == 0][0]

                    # Thực hiện từng di chuyển trong giải pháp
                    if move == "right" and empty_col > 0:
                        temp_grid[empty_row][empty_col], temp_grid[empty_row][empty_col - 1] = temp_grid[empty_row][
                            empty_col - 1], temp_grid[empty_row][empty_col]
                    elif move == "left" and empty_col < GAME_SIZE - 1:
                        temp_grid[empty_row][empty_col], temp_grid[empty_row][empty_col + 1] = temp_grid[empty_row][
                            empty_col + 1], temp_grid[empty_row][empty_col]
                    elif move == "up" and empty_row < GAME_SIZE - 1:
                        temp_grid[empty_row][empty_col], temp_grid[empty_row + 1][empty_col] = temp_grid[empty_row + 1][
                            empty_col], temp_grid[empty_row][empty_col]
                    elif move == "down" and empty_row > 0:
                        temp_grid[empty_row][empty_col], temp_grid[empty_row - 1][empty_col] = temp_grid[empty_row - 1][
                            empty_col], temp_grid[empty_row][empty_col]

                # Kiểm tra xem lưới tạm có đúng không
                if temp_grid == self.tiles_grid_completed:
                    print("Found correct solution")
                    return solution_moves

            print("Máy học chưa đủ.")
            return None

        except Exception as e:
            print(f"Error reading CSV: {e}")
            return None

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                self.csv_file.close()
                quit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                for row, tiles in enumerate(self.tiles):
                    for col, tile in enumerate(tiles):
                        if tile.click(mouse_x, mouse_y):
                            if tile.right() and self.tiles_grid[row][col + 1] == 0:
                                self.tiles_grid[row][col], self.tiles_grid[row][col + 1] = self.tiles_grid[row][col + 1], self.tiles_grid[row][col]
                            elif tile.left() and self.tiles_grid[row][col - 1] == 0:
                                self.tiles_grid[row][col], self.tiles_grid[row][col - 1] = self.tiles_grid[row][col - 1], self.tiles_grid[row][col]
                            elif tile.up() and self.tiles_grid[row - 1][col] == 0:
                                self.tiles_grid[row][col], self.tiles_grid[row - 1][col] = self.tiles_grid[row - 1][col], self.tiles_grid[row][col]
                            elif tile.down() and self.tiles_grid[row + 1][col] == 0:
                                self.tiles_grid[row][col], self.tiles_grid[row + 1][col] = self.tiles_grid[row + 1][col], self.tiles_grid[row][col]
                            self.draw_tiles()
                            self.save_grid_to_csv()

                for button in self.buttons_list:
                    if button.click(mouse_x, mouse_y):
                        if button.text == "Shuffle":
                            self.shuffle_time = 0
                            self.start_shuffle = True
                        elif button.text == "Reset":
                            self.new()
                        elif button.text == "Giai":
                            self.solve_puzzle()
                        elif button.text == "Hocmay":
                            solution_moves = self.load_solution_from_csv()
                            if solution_moves is not None:
                                self.solution_moves = solution_moves
                                self.solution_index = 0
                                self.is_machine_solving = True  # Activate machine solving mode
                                self.start_timer = False  # Stop the manual game timer
                            else:
                                print("Học Chưa Đủ.")

    def draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(pygame.font.match_font(FONT_NAME), size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

game = Game()
while True:
    game.new()
    game.run()
