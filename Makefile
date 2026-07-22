.PHONY: clean

ifeq ($(OS),Windows_NT)
RM = cmd /C del /f /q
else
RM = rm -f
endif

clean:
	-$(RM) transactions.csv
