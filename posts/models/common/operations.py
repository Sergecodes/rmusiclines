

class PostOperations:
    def get_ratings(self) -> dict[int, int]:
        """Return ratings of post as a dictionary of star_count: num_of_stars"""
        ratings_dict = {1: 0, 3: 0, 5: 0}
        
        for rating in self.ratings.all():
            num_stars = rating.num_stars
            ratings_dict[num_stars] = ratings_dict[num_stars] + 1

        return ratings_dict



    
    