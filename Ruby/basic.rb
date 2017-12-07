#Simple program to take a user's first and last name plus their year of birth and generate a userID.

puts "First Name:"
first_name = gets.chomp
puts "Last Name:"
last_name = gets.chomp
puts "Year of birth:"
yob = gets.chomp

user_id = first_name[0].downcase + last_name.downcase + yob.to_s
puts "Your User ID is  #{user_id}"

family = {
    "Deonn" => 29,
    "Jamal" => 24,
    "Javon" => 20,
    "Shemaiah" => 13
}

family.each do |name, age|
  puts "#{name} is currently #{age} years old"
end

puts "FYI - The gift you buy a person depends on their character"
present = gets.chomp

case present
  when "Deonn"
    puts "AUDI or BMW"
  when "Jamal"
    puts "Cosy 3-4 bed house, all expenses paid"
  when "Javon"
    puts "Trainers and cash ££$$££$$"
  when "Shemaiah"
    puts "Money and trainers"
  else
    puts "No idea mate"
end

def yeelder
  puts "Only prints this and whatever you pass me in a block"
end

yeelder

