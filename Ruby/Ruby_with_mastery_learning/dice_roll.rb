#Simple dice roll program

puts "Welcome to the dice rolling game"
puts "Are you ready to roll ? "
answer = gets.chomp

def rand_num_gen()
  return rand(1..7)
end

if answer = answer.casecmp("yes") == 0
  puts "You've rolled a #{rand_num_gen}"
else
  puts "Ok, come back when you're ready to play"
end

