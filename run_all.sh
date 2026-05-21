for plik in tests/*; do
	if [ -f "$plik" ]; then
		if [ "${plik: -3}" = ".in" ]; then
			python3 poker_test.py "$plik" "${plik:0:-3}.out"
		fi
	fi
done
