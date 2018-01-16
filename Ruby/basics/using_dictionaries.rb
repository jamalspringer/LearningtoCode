
# animals = {
#
# "bear" => "a creature that fishes in the river for salmon.",
# "river" => "a body of water that contains salmon, and sometimes bears.",
# "salmon" => "a fish, sometimes in a river, sometimes in a bear, and sometimes in both."
#
# }
#
# input = gets.chomp.to_s
#
# puts animals[input]

# =========================================

players = [
    { :name => "Sam", :sport => "tennis" },
    { :name => "Mary", :sport => "squash" },
    { :name => "Ed", :sport => "tennis" },
    { :name => "Mark", :sport => "football" }
]

players_by_sport = {}

players.each do |player|
  sport = player[:sport]

  if players_by_sport[sport] == nil
    players_by_sport[sport] = []
  end

  players_by_sport[sport].push(player[:name])
end

puts players_by_sport