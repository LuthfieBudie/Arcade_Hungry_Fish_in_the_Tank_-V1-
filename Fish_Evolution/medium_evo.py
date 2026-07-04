


def check_medium_evolution(player):
    if player.score >= 500:
        player.status = "HUGE"
        player.width = 160  
        player.height = 80
        print("Evolution")