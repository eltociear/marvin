import marvin
import pydantic
import pytest
from marvin import Bot
from marvin.bots.response_formatters import ResponseFormatter
from marvin.utilities.types import format_type_str


class TestCreateBots:
    async def test_create_bot_with_default_settings(self):
        bot = Bot()
        assert bot.name == marvin.bots.base.DEFAULT_NAME
        assert bot.personality == marvin.bots.base.DEFAULT_PERSONALITY
        assert bot.instructions == marvin.bots.base.DEFAULT_INSTRUCTIONS

    async def test_create_bot_with_custom_name(self):
        bot = Bot(name="Test Bot")
        assert bot.name == "Test Bot"
        assert bot.personality == marvin.bots.base.DEFAULT_PERSONALITY
        assert bot.instructions == marvin.bots.base.DEFAULT_INSTRUCTIONS

    async def test_create_bot_with_custom_personality(self):
        bot = Bot(personality="Test Personality")
        assert bot.name == marvin.bots.base.DEFAULT_NAME
        assert bot.personality == "Test Personality"
        assert bot.instructions == marvin.bots.base.DEFAULT_INSTRUCTIONS

    async def test_create_bot_with_custom_instructions(self):
        bot = Bot(instructions="Test Instructions")
        assert bot.name == marvin.bots.base.DEFAULT_NAME
        assert bot.personality == marvin.bots.base.DEFAULT_PERSONALITY
        assert bot.instructions == "Test Instructions"


class TestSaveBots:
    async def test_save_bot(self):
        bot = Bot()
        await bot.save()
        loaded_bot = await Bot.load(bot.name)
        for attr in ["id", "name", "personality", "instructions", "plugins"]:
            assert getattr(loaded_bot, attr) == getattr(bot, attr)

    async def test_save_custom_bot(self):
        bot = Bot(
            name="Test Bot",
            personality="Test Personality",
            instructions="Test Instructions",
        )
        await bot.save()
        loaded_bot = await Bot.load(bot.name)
        for attr in ["id", "name", "personality", "instructions", "plugins"]:
            assert getattr(loaded_bot, attr) == getattr(bot, attr)

    async def test_save_bot_with_plugins(self):
        bot = Bot(
            plugins=[
                marvin.plugins.mathematics.Calculator(),
                marvin.plugins.web.VisitURL(),
            ]
        )
        await bot.save()
        loaded_bot = await Bot.load(bot.name)
        assert loaded_bot.plugins == bot.plugins

    async def test_save_bot_with_custom_plugins(self):
        @marvin.plugin
        def my_plugin(x: int):
            """adds one to a number"""
            return x + 1

        bot = Bot(plugins=[my_plugin])
        await bot.save()
        loaded_bot = await Bot.load(bot.name)
        assert loaded_bot.plugins == bot.plugins

    async def test_save_bot_with_existing_name(self):
        await Bot().save()
        with pytest.raises(ValueError, match="(already exists)"):
            await Bot().save()

    async def test_save_bot_with_existing_custom_name(self):
        await Bot(name="abc").save()
        with pytest.raises(ValueError, match="(already exists)"):
            await Bot(name="abc").save()

    async def test_overwrite_bot(self):
        bot1 = Bot(instructions="1")
        bot2 = Bot(instructions="2")
        await bot1.save()
        await bot2.save(overwrite=True)
        loaded_bot = await Bot.load(bot1.name)
        assert loaded_bot.instructions == bot2.instructions


class TestResponseFormat:
    async def test_default_response_formatter(self):
        bot = Bot()
        assert isinstance(bot.response_format, ResponseFormatter)

        assert bot.response_format.validate_response("hello") is None

    async def test_response_formatter_from_string(self):
        bot = Bot(response_format="list of strings")
        assert isinstance(
            bot.response_format, marvin.bots.response_formatters.ResponseFormatter
        )

        assert bot.response_format.format == "list of strings"

    async def test_response_formatter_from_json_string(self):
        bot = Bot(response_format="JSON list of strings")
        assert isinstance(
            bot.response_format, marvin.bots.response_formatters.JSONFormatter
        )

        assert bot.response_format.format == "JSON list of strings"

    @pytest.mark.parametrize("type_", [list, list[str], dict[str, int], int])
    async def test_response_formatter_from_python_types(self, type_):
        bot = Bot(response_format=type_)
        assert isinstance(
            bot.response_format, marvin.bots.response_formatters.TypeFormatter
        )

        assert format_type_str(type_) in bot.response_format.format

    async def test_pydantic_response_format(self):
        class OutputFormat(pydantic.BaseModel):
            x: int
            y: str = pydantic.Field(
                description=(
                    'The "written" version of the number x. For example, if x is 1,'
                    ' then y is "one".'
                )
            )

        bot = Bot(response_format=OutputFormat)
        assert isinstance(
            bot.response_format, marvin.bots.response_formatters.PydanticFormatter
        )
        assert bot.response_format.format.startswith(
            "A JSON object that satisfies the following OpenAPI schema:"
        )
        assert str(OutputFormat.schema_json()) in bot.response_format.format
