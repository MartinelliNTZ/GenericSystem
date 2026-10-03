from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Team:
    """Representa um time em um jogo."""
    id: int
    name: str
    logo: str
    winner: Optional[bool] = None

    def __str__(self) -> str:
        return self.name


@dataclass
class League:
    """Representa uma liga/competição."""
    id: int
    name: str
    country: str
    logo: str
    season: int
    round: Optional[str] = None

    def __str__(self) -> str:
        if self.round:
            return f"{self.name} - {self.round}"
        return self.name


@dataclass
class Score:
    """Representa o placar em diferentes fases do jogo."""
    halftime_home: Optional[int]
    halftime_away: Optional[int]
    fulltime_home: Optional[int]
    fulltime_away: Optional[int]
    penalty_home: Optional[int] = None
    penalty_away: Optional[int] = None
    extratime_home: Optional[int] = None
    extratime_away: Optional[int] = None

    def get_result_string(self) -> str:
        """Retorna o placar em formato de string."""
        if self.fulltime_home is not None and self.fulltime_away is not None:
            return f"{self.fulltime_home}-{self.fulltime_away}"
        elif self.penalty_home is not None and self.penalty_away is not None:
            return f"({self.penalty_home}-{self.penalty_away})"
        else:
            return "-"


@dataclass
class Fixture:
    """Representa uma fixture (jogo)."""
    id: int
    home_team: Team
    away_team: Team
    league: League
    date: str
    date_time: datetime
    score: Score
    status: str
    status_long: str
    referee: Optional[str] = None
    venue: Optional[str] = None
    city: Optional[str] = None

    def get_time(self) -> str:
        """Retorna a hora de início do jogo em HH:MM."""
        try:
            return self.date_time.strftime("%H:%M")
        except Exception:
            return ""

    def get_date(self) -> str:
        """Retorna a data em formato YYYY-MM-DD."""
        return self.date[:10] if self.date else ""

    def get_display_name(self) -> str:
        """Retorna o nome formatado do jogo."""
        return f"{self.home_team.name} vs {self.away_team.name}"

    def __str__(self) -> str:
        return f"[{self.get_date()} {self.get_time()}] {self.home_team.name} {self.score.get_result_string()} {self.away_team.name} ({self.league.name})"

    @classmethod
    def from_api_response(cls, fixture_data: dict) -> "Fixture":
        """Cria uma instância de Fixture a partir da resposta da API."""
        fixture_info = fixture_data.get("fixture", {})
        league_info = fixture_data.get("league", {})
        teams_info = fixture_data.get("teams", {})
        score_info = fixture_data.get("score", {})

        # Extrair dados de times
        home_data = teams_info.get("home", {})
        away_data = teams_info.get("away", {})

        home_team = Team(
            id=home_data.get("id", 0),
            name=home_data.get("name", ""),
            logo=home_data.get("logo", ""),
            winner=home_data.get("winner"),
        )

        away_team = Team(
            id=away_data.get("id", 0),
            name=away_data.get("name", ""),
            logo=away_data.get("logo", ""),
            winner=away_data.get("winner"),
        )

        # Extrair dados de liga
        league = League(
            id=league_info.get("id", 0),
            name=league_info.get("name", ""),
            country=league_info.get("country", ""),
            logo=league_info.get("logo", ""),
            season=league_info.get("season", 0),
            round=league_info.get("round"),
        )

        # Extrair dados de placar
        halftime = score_info.get("halftime", {})
        fulltime = score_info.get("fulltime", {})
        penalty = score_info.get("penalty", {})
        extratime = score_info.get("extratime", {})

        score = Score(
            halftime_home=halftime.get("home"),
            halftime_away=halftime.get("away"),
            fulltime_home=fulltime.get("home"),
            fulltime_away=fulltime.get("away"),
            penalty_home=penalty.get("home"),
            penalty_away=penalty.get("away"),
            extratime_home=extratime.get("home"),
            extratime_away=extratime.get("away"),
        )

        # Extrair dados de status
        status_info = fixture_info.get("status", {})

        # Extrair data como datetime
        date_str = fixture_info.get("date", "")
        try:
            date_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            date_time = datetime.now()

        return cls(
            id=fixture_info.get("id", 0),
            home_team=home_team,
            away_team=away_team,
            league=league,
            date=date_str,
            date_time=date_time,
            score=score,
            status=status_info.get("short", ""),
            status_long=status_info.get("long", ""),
            referee=fixture_info.get("referee"),
            venue=fixture_info.get("venue", {}).get("name"),
            city=fixture_info.get("venue", {}).get("city"),
        )
