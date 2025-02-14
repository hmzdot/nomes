
# Tic-Tac-Toe game

# Initialize the board
board = [' ' for _ in range(9)]

# Function to print the board
def print_board():
    row1 = f'{board[0]} | {board[1]} | {board[2]}'
    row2 = f'{board[3]} | {board[4]} | {board[5]}'
    row3 = f'{board[6]} | {board[7]} | {board[8]}'
    print(row1)
    print('-' * 9)
    print(row2)
    print('-' * 9)
    print(row3)

# Function to check for a win
def check_win(player):
    win_conditions = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8), 
        (0, 3, 6), (1, 4, 7), (2, 5, 8), 
        (0, 4, 8), (2, 4, 6)
    ]
    for condition in win_conditions:
        if board[condition[0]] == board[condition[1]] == board[condition[2]] == player:
            return True
    return False

# Function to check for a tie
def check_tie():
    return ' ' not in board

# Main game loop
def main():
    current_player = 'X'
    while True:
        print_board()
        move = int(input(f'Enter a move (0-8) for player {current_player}: '))
        if board[move] == ' ':
            board[move] = current_player
            if check_win(current_player):
                print_board()
                print(f'Player {current_player} wins!')
                break
            elif check_tie():
                print_board()
                print('The game is a tie!')
                break
            current_player = 'O' if current_player == 'X' else 'X'
        else:
            print('Invalid move, try again.')

if __name__ == '__main__':
    main()