"""
Lưu trữ tất cả những thông tin về trạng thái game
Quyết định những bước di chuyển hợp lệ từ trạng thái hiện tại
Giúp lưu trữ nhật ký các bước đi
"""


class GameState:
    def __init__(self): #phuong thuc khoi tao
        """
        Bàn cờ (board) có dạng 2d-list kích thước 8x8, mỗi thành phần trong list sẽ có 2 thuộc tinh
        Thuộc tính đầu tiên biểu diễn cho màu sắc của quân cờ: 'b' = black hay 'w' = 'white'
        Thuộc tính thứ hai biểu diễn cho loại quân cờ: 'R' = Rook(xe); 'N' = Knight(mã);
        'B' = Bishop(tịnh); 'Q' = Queen(Hậu); 'K' = King(vua); 'p' = pawn(tốt).
        "--" biểu diễn cho khoảng trống không chứa quân cờ nào.
        """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {"p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getKnightMoves,
                              "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}
        self.white_to_move = True # Quân trắng đi trước
        self.move_log = []  # Nhật ký di chuyển
        self.white_king_location = (7, 4)  # Đầu trận quân wK ở hàng 8, cột 5 -> (7,4)
        self.black_king_location = (0, 4)  # Khởi tạo bK ở hàng 1, cot 5 -> (0,4)
        self.checkmate = False
        self.stalemate = False  # Hết đường đi
        self.in_check = False
        self.pins = [] # ghim quân
        self.checks = []
        self.enpassant_possible = ()  # lưu trữ những ô mà có thể thực hiện en-passant;
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castling_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                               self.current_castling_rights.wqs, self.current_castling_rights.bqs)]

    def makeMove(self, move):
        """
        Mỗi chuyển động (Move) như 1 tham số để thực thi
        (không có tác dụng với các trường hợp đặc biệt như nhập thành (castling), phong hậu (pawn promotion) và
        bắt tốt qua đường (en-passant)
        """
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved #giá trị đích mà quân cờ đến chính là vị trí quân cờ đến
        self.move_log.append(move)  # Ghi lại nhật kí để có thể hoàn tác (undo)
        self.white_to_move = not self.white_to_move  # Chuyển lượt cho đối phương
        # cập nhật vị trí của quân vua nếu vua được di chuyển
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # về phong hậu
        if move.is_pawn_promotion:
            # if not is_AI:
            #    promoted_piece = input("Promote to Q, R, B, or N:") #take this to UI later
            #    self.board[move.end_row][move.end_col] = move.piece_moved[0] + promoted_piece
            # else:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"

        # về luật bắt tốt qua đường
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--"  # bắt tốt 

        # cập nhật biến enpassant_possible
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:  # only on 2 square pawn advance
            self.enpassant_possible = ((move.start_row + move.end_row) // 2, move.start_col)
        else:
            self.enpassant_possible = ()

        # di chuyển nhập thành (Castle)
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # nhập thành với xe ở phía gần vua (Kingside castling)
                self.board[move.end_row][move.end_col - 1] = self.board[move.end_row][
                    move.end_col + 1]  # di chuyển quân xe sang ô mới
                self.board[move.end_row][move.end_col + 1] = '--'  # xóa bỏ xe cũ
            else:  # nhập thành với xe ở bên gần phía quân hậu (Queenside castling)
                self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][
                    move.end_col - 2]
                self.board[move.end_row][move.end_col - 2] = '--'

        self.enpassant_possible_log.append(self.enpassant_possible)

        # cập nhật luật hợp thành - bất cứ khi nào có 1 chuyển động của xe hoặc vua
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                                   self.current_castling_rights.wqs, self.current_castling_rights.bqs))

    def undoMove(self):
        """
        Hoàn tác lại bước di chuyển cuối
        """
        if len(self.move_log) != 0:  # đảm bảo rằng đã có ít nhất 1 bước di chuyển
            move = self.move_log.pop() # loại bỏ bước di chuyển cuối cùng trong nhật ký
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move  # swap players
            # cập nhật vị trí vua nếu cần
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)
            # đi lại nước bắt tốt qua đường (en-passant)
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"  # đặt lại ô trống
                self.board[move.start_row][move.end_col] = move.piece_captured

            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1]

            # hoàn tác quyền castle
            self.castle_rights_log.pop()  # loại bỏ quyền castle mới ra khỏi bước đi đang hoàn tác
            self.current_castling_rights = self.castle_rights_log[-1]  # đặt quyền castle hiện tại thành quyền castle cuối cùng đuược lưu trong danh sách
            # hoàn tác castle
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # castle phía bên vua
                    self.board[move.end_row][move.end_col + 1] = self.board[move.end_row][move.end_col - 1]
                    self.board[move.end_row][move.end_col - 1] = '--'
                else:  # castle phía bên hậu (Queen-side castling)
                    self.board[move.end_row][move.end_col - 2] = self.board[move.end_row][move.end_col + 1]
                    self.board[move.end_row][move.end_col + 1] = '--'
            self.checkmate = False
            self.stalemate = False

    def updateCastleRights(self, move):
        """
        Cập nhật quyền castle (nhập thành) - quân xe hoặc vua di chuyển trước khi nhập thành thì sẽ không thể
        thực hiện nhập thành.
        """
        # quân xe bị ăn mất trước khi castle -> mất quyền castle
        if move.piece_captured == "wR":
            if move.end_col == 0:  # quân xe trắng bên trái
                self.current_castling_rights.wqs = False
            elif move.end_col == 7:  # quân xe trắng bên phải
                self.current_castling_rights.wks = False
        elif move.piece_captured == "bR":
            if move.end_col == 0:  # quân xe đen bên trái
                self.current_castling_rights.bqs = False
            elif move.end_col == 7:  # quân xe đen bên phải
                self.current_castling_rights.bks = False

        # quân xe hoặc vua di chuyển trước khi castle -> mất quyền castle
        if move.piece_moved == 'wK': # vua trắng
            self.current_castling_rights.wqs = False
            self.current_castling_rights.wks = False
        elif move.piece_moved == 'bK': # vua đen
            self.current_castling_rights.bqs = False
            self.current_castling_rights.bks = False
        elif move.piece_moved == 'wR':
            if move.start_row == 7:
                if move.start_col == 0:  # xe trái
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:  # xe phải
                    self.current_castling_rights.wks = False
        elif move.piece_moved == 'bR':
            if move.start_row == 0:
                if move.start_col == 0:  # xe trái
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:  # xe phải
                    self.current_castling_rights.bks = False

    def getValidMoves(self):
        """
        Kiểm tra những di chuyển hợp lệ.
        """
        temp_castle_rights = CastleRights(self.current_castling_rights.wks, self.current_castling_rights.bks,
                                          self.current_castling_rights.wqs, self.current_castling_rights.bqs)
        # thuật toán
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()
        # in_check: các chiếu khác nhau, pins: các cản trở chiếu, checks: trả về thông tin chiếu

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]
        if self.in_check:
            if len(self.checks) == 1:  # nếu chỉ có 1 chiếu thì chặn chiếu đó hoặc di chuyển vua.
                moves = self.getAllPossibleMoves()
                # để chặn chiếu -> đặt 1 quân cờ vào 1 trong những vị trí ở giữa cờ chiếu của đối thủ và vua của bạn
                check = self.checks[0]  # kiểm tra thông tin
                check_row = check[0]
                check_col = check[1]
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # những ô mà quân cờ có thể đi

                # nếu là quân mã, phải bắt mã hoặc di chuyển vua, không có quân cờ nào khác có thể đi.
                if piece_checking[1] == "N":
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        valid_square = (king_row + check[2] * i,
                                        king_col + check[3] * i)  # check[2] và check[3] là hướng tần công
                        valid_squares.append(valid_square)
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            # di chuyển đến ô của quân cờ đang tấn công thì thoát vòng lặp.
                            break
                # loại bỏ tất cả các di chuyển mà không phải cản chiếu hay di chuyển vua.
                for i in range(len(moves) - 1, -1, -1):  # lặp lại danh sách các nước đi từ cuối lên
                    if moves[i].piece_moved[1] != "K":  # không di chuyển vua nên nước đi phải chặn chiếu hoặc bắt quân chiếu
                        if not (moves[i].end_row,
                                moves[i].end_col) in valid_squares:  # bước đi không chặn hay bắt quân chiếu -> loại bỏ
                            moves.remove(moves[i])
            else:  # chiếu đôi, bắt buộc di chuyển vua
                self.getKingMoves(king_row, king_col, moves)
        else:  # không bị chiếu -> đi tùy ý
            moves = self.getAllPossibleMoves()
            if self.white_to_move:
                self.getCastleMoves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.getCastleMoves(self.black_king_location[0], self.black_king_location[1], moves)

        if len(moves) == 0:
            if self.inCheck():
                self.checkmate = True
            else:
                self.stalemate = True
        else:
            self.checkmate = False
            self.stalemate = False

        self.current_castling_rights = temp_castle_rights
        return moves

    def inCheck(self):
        """
        Chỉ ra nếu 1 người chơi hiện tại đang bị chiếu tướng - trả về true nếu bị chiếu, false nếu không.
        """
        if self.white_to_move:
            return self.squareUnderAttack(self.white_king_location[0], self.white_king_location[1])
        else:
            return self.squareUnderAttack(self.black_king_location[0], self.black_king_location[1])

    def squareUnderAttack(self, row, col):
        """
        Chỉ ra nếu đối phương có thể tấn công vào ô nào.
        """
        self.white_to_move = not self.white_to_move  # đổi sang góc nhìn của đối thủ
        opponents_moves = self.getAllPossibleMoves()
        self.white_to_move = not self.white_to_move
        for move in opponents_moves:
            if move.end_row == row and move.end_col == col:  # ô nào đó đang có nguy cơ bị tấn công
                return True
        return False

    def getAllPossibleMoves(self):
        """
        Di chuyển tự do mà không cần kiểm tra chiếu tướng
        """
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]
                if (turn == "w" and self.white_to_move) or (turn == "b" and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.moveFunctions[piece](row, col, moves)  # gọi đến hàm di chuyển hợp lệ với từng quân cờ
        return moves

    def checkForPinsAndChecks(self):
        pins = []  # những ô bị ghim ;
        checks = []  # những ô đang bị đối thủ chiếu ;
        in_check = False
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        # kiểm tra quân cờ có bị ghim hay chiếu tướng không , theo dõi ghim (hướng của quân cờ và vị trí các quân cờ có thể chiếu tướng);
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # reset những quân bị ghim
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():  # quân đồng minh đầu tiên có thể bị ghim
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        else:  # quân đồng minh thứ 2 - không chiếu hay ghim ở vị trí này
                            break
                    elif end_piece[0] == enemy_color:
                        enemy_type = end_piece[1]
                        # có 5 trường hợp có thể xảy ra khi quân vua bị ghim và các quân cờ có thể tác động đến;
                        # 1.) nước đi đang xét nằm trên hàng ngang hoặc dọc xa vua và quân cờ là quân xe ;
                        # 2.) nước đi đang xét nằm trên đường chéo xa vua và quân cờ là quân tượng ;
                        # 3.) nước đi cách vua 1 ô theo đường chéo và quân cờ là quân tốt ;
                        # 4.) bất kì hướng nào khi quân cờ là quân hậu ;
                        # 5.) bất kì hướng nào khi quân cờ là quân vua cách vua 1 ô .
                        if (0 <= j <= 3 and enemy_type == "R") or (4 <= j <= 7 and enemy_type == "B") or (
                                i == 1 and enemy_type == "p" and (
                                (enemy_color == "w" and 6 <= j <= 7) or (enemy_color == "b" and 4 <= j <= 5))) or (
                                enemy_type == "Q") or (i == 1 and enemy_type == "K"):
                            if possible_pin == ():  # không có quân chặn -> chiếu tướng
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  # quân cờ chặn -> bị ghim ;
                                pins.append(possible_pin)
                                break
                        else:  # quân đối thủ không chiếu tướng;
                            break
                else:
                    break  # kết thúc vòng lặp
        # Kiểm tra mã chiếu tướng;
        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2), (1, -2))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == "N":  # quân mã đối thủ đang chiếu tướng;
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))
        return in_check, pins, checks

    def getPawnMoves(self, row, col, moves):
        """
        Lấy tất cả các bước di chuyển của quân Tốt đang nằm ở cột, hàng và thêm chuyển động vào list
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[row + move_amount][col] == "--":  # tốt đi 1 ô
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row + 2 * move_amount][col] == "--":  # tốt đi 2 ô
                    moves.append(Move((row, col), (row + 2 * move_amount, col), self.board))
        if col - 1 >= 0:  # quân tốt tấn công theo đường chéo trái
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col - 1), self.board))
                if (row + move_amount, col - 1) == self.enpassant_possible:
                    # kiểm tra quân tốt có thể thực hiện enpassant không - không có quân nào chặn tốt
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # vua nằm bên trái quân tốt
                            # inside: giữa quân vua và quân tốt;
                            # outside: giữa quân tốt với biên
                            inside_range = range(king_col + 1, col - 1)
                            outside_range = range(col + 1, 8)
                        else:  # vua nằm bên phải quân tốt
                            inside_range = range(king_col - 1, col, -1)
                            outside_range = range(col - 2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # kiểm tra có quân cờ nào đứng cạnh quân tốt được chọn
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col - 1), self.board, is_enpassant_move=True))
        if col + 1 <= 7:  # quân tốt thực hiện ăn phải
            if not piece_pinned or pin_direction == (move_amount, +1):
                if self.board[row + move_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col + 1), self.board))
                if (row + move_amount, col + 1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col:  # quân vua ở bên trái quân tốt
                            # inside: giữa vua và tốt ;
                            # outside: giữa tốt và biên ;
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col + 2, 8)
                        else:  # vua nằm bên phải quân tốt
                            inside_range = range(king_col - 1, col + 1, -1)
                            outside_range = range(col - 1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "--":  # some piece beside en-passant pawn blocks
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == "R" or square[1] == "Q"):
                                attacking_piece = True
                            elif square != "--":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:
                        moves.append(Move((row, col), (row + move_amount, col + 1), self.board, is_enpassant_move=True))

    def getRookMoves(self, row, col, moves):
        """
        Các di chuyển hợp lệ của quân Xe (Rook) và thêm những di chuyển ấy vào list
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != "Q":  #  can't remove queen from pin on rook moves, only remove it on bishop moves
                    self.pins.remove(self.pins[i]) # loại bỏ ghim
                break

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))  # up, left, down, right
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # kiểm tra những hướng đi chỉ nằm trong bàn cờ
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]  # nếu bị ghim thì đi theo hướng ghim hoặc ngược hướng ghim mới được thực hiện;
                        if end_piece == "--":  # đi vào ô trống
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # bắt lấy quân đối thủ
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # quân đồng minh
                            break
                else:  # off board
                    break

    def getKnightMoves(self, row, col, moves):
        """
        Các di chuyển hợp lệ của quân Mã (Knight) và thêm những di chuyển ấy vào list
        """
        # check pins
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = ((-2, -1), (-2, 1), (-1, 2), (1, 2), (2, -1), (2, 1), (-1, -2),
                        (1, -2))  # up/left, up/right, right/up, right/down, down/left, down/right, left/up, left/down
        ally_color = "w" if self.white_to_move else "b"
        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:  # nếu ô đích trống hoặc có đối thủ thì thêm vào danh sách bước đi hợp lệ
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):
        """
        Các di chuyển hợp lệ của quân Tịnh (Bishop) và thêm những di chuyển ấy vào list
        """
        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # diagonals (đường chéo) : up/left, up/right, down/right, down/left
        enemy_color = "b" if self.white_to_move else "w"
        for direction in directions:
            for i in range(1, 8):
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # kiểm tra move trong phạm vi bàn cờ ;
                    if not piece_pinned or pin_direction == direction or pin_direction == (
                            -direction[0], -direction[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "--":  # di chuyển hợp lệ vào ô trống;
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:  # bắt quân đối thủ;
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # quân đồng minh
                            break
                else:  # off board
                    break

    def getQueenMoves(self, row, col, moves):
        """
        Các di chuyển của quân Hậu (Queen) là hợp thành bởi các di chuyển của quân Tịnh (Bishop) và quân Xe (Rook)
        """
        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):
        """
        Các di chuyển hợp lệ của quân Vua (King) và thêm những di chuyển ấy vào list
        """
        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"
        for i in range(8):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:  # không là quân cờ đồng minh - ô trống hoặc cờ đối thủ ;
                    # đặt Vua ở ô đích và kiểm tra xem có chiếu không ;
                    if ally_color == "w":
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # place king back on original location
                    if ally_color == "w":
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    def getCastleMoves(self, row, col, moves):
        """
        Tạo các nước castle hợp lệ cho quân Vua và thêm vào danh sách moves
        """
        if self.squareUnderAttack(row, col):
            return  # không thể castle khi bị chiếu;
        if (self.white_to_move and self.current_castling_rights.wks) or (
                not self.white_to_move and self.current_castling_rights.bks):
            self.getKingsideCastleMoves(row, col, moves)
        if (self.white_to_move and self.current_castling_rights.wqs) or (
                not self.white_to_move and self.current_castling_rights.bqs):
            self.getQueensideCastleMoves(row, col, moves)

    def getKingsideCastleMoves(self, row, col, moves):
        if self.board[row][col + 1] == '--' and self.board[row][col + 2] == '--':
            if not self.squareUnderAttack(row, col + 1) and not self.squareUnderAttack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castle_move=True))

    def getQueensideCastleMoves(self, row, col, moves):
        if self.board[row][col - 1] == '--' and self.board[row][col - 2] == '--' and self.board[row][col - 3] == '--':
            if not self.squareUnderAttack(row, col - 1) and not self.squareUnderAttack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castle_move=True))


class CastleRights:
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    """
    Trong cờ vua, các ô trên bàn cờ được mô tả bởi 2 ký tự, một trong số đó là chữ số từ 1-8 (tương ứng với các hàng)
    và còn lại là các ky tự từ a-f (tương ứng với cột), để sử dụng những ký hiệu đó, ta cần ánh xạ tọa độ [row][col]
    sao cho phù hợp với những người sử dụng trong trò cờ vua gốc
    """

    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {"a": 0, "b": 1, "c": 2, "d": 3,
                     "e": 4, "f": 5, "g": 6, "h": 7}
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, start_square, end_square, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row = start_square[0]
        self.start_col = start_square[1]
        self.end_row = end_square[0]
        self.end_col = end_square[1]
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]
        # phong hậu
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
                self.piece_moved == "bp" and self.end_row == 7)
        # en passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wp" if self.piece_moved == "bp" else "bp"
        # nhập thành
        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "--"
        self.moveID = self.start_row * 1000 + self.start_col * 100 + self.end_row * 10 + self.end_col

    def __eq__(self, other):
        """
        Overriding the equals method.
        """
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        if self.is_pawn_promotion:
            return self.getRankFile(self.end_row, self.end_col) + "Q"
        if self.is_castle_move:
            if self.end_col == 1:
                return "0-0-0"
            else:
                return "0-0"
        if self.is_enpassant_move:
            return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                self.end_col) + " e.p."
        if self.piece_captured != "--":
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.start_row, self.start_col)[0] + "x" + self.getRankFile(self.end_row,
                                                                                                    self.end_col)
            else:
                return self.piece_moved[1] + "x" + self.getRankFile(self.end_row, self.end_col)
        else:
            if self.piece_moved[1] == "p":
                return self.getRankFile(self.end_row, self.end_col)
            else:
                return self.piece_moved[1] + self.getRankFile(self.end_row, self.end_col)

        # TODO Disambiguating moves

    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    def __str__(self):
        if self.is_castle_move:
            return "0-0" if self.end_col == 6 else "0-0-0"

        end_square = self.getRankFile(self.end_row, self.end_col)

        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square + "Q" if self.is_pawn_promotion else end_square

        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += "x"
        return move_string + end_square
