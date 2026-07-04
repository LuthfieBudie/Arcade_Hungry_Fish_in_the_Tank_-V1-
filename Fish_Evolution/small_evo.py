


def check_small_evolution(player):
    if player.score >= 100:
        player.status = "MEDIUM"
        player.width = 100  
        player.height = 50
        print("Evolution")