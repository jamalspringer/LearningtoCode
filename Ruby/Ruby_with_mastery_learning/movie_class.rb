class Movie
  def initialize(title, director, genre, duration, year, gross)
    @title = title
    @director = director
    @genre = genre
    @duration = duration
    @year = year
    @gross = gross
  end

genres = [:Action, :Comedy, :Romantic, :Thriller, :Horror]

public

  def title?
    return @title
  end

  def director?
    return @director
  end

  def genre?
    return @genre
  end

  def duration?
    return @duration
  end

  def year?
    return @year
  end

  def gross?
    return @gross
  end

end
