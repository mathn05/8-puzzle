import random

from src.core.puzzle import GOAL_STATE, is_solvable


def to_tuple_state(state):
	return tuple(tuple(row) for row in state)


def validate_board(state):
	if len(state) != 3 or any(len(row) != 3 for row in state):
		return False, "Bảng phải có đúng 3 hàng và 3 cột."

	flat = [value for row in state for value in row]
	if any(not isinstance(value, int) for value in flat):
		return False, "Bảng chỉ được chứa số nguyên."

	values = sorted(flat)
	if values != list(range(9)):
		return False, "Bảng phải chứa đủ các số từ 0 đến 8, không trùng lặp."

	return True, ""


def parse_board_input(text):
	normalized = text.replace(",", " ")
	parts = [item for item in normalized.split() if item]

	if len(parts) != 9:
		return None, "Bạn cần nhập đúng 9 số."

	try:
		numbers = [int(item) for item in parts]
	except ValueError:
		return None, "Chỉ nhập số từ 0 đến 8."

	rows = [numbers[i : i + 3] for i in range(0, 9, 3)]
	is_valid, error = validate_board(rows)
	if not is_valid:
		return None, error

	return to_tuple_state(rows), ""


def generate_random_solvable():
	nums = list(range(9))
	while True:
		random.shuffle(nums)
		rows = [nums[i : i + 3] for i in range(0, 9, 3)]
		state = to_tuple_state(rows)
		if state != GOAL_STATE and is_solvable(state):
			return state


