import logging
from datetime import datetime

from peewee import *


database = SqliteDatabase('data.db',pragmas={'foreign_keys': 1})

logger = logging.getLogger('nym')

def create_tables():
    with database:
        database.create_tables([User, Mixnode])


class BaseModel(Model):
    class Meta:
        database = database

    def connect(self):
        logHandler = logging.getLogger('nym')

        try:
            database.connect()
        except Exception as e:
            logHandler.exception(e)

    def close(self):
        logHandler = logging.getLogger('nym')

        try:
            database.close()
        except Exception as e:
            logHandler.exception(e)

    def insertUser(self, userid, mixnodeid, state):
        logHandler = logging.getLogger('nym')

        self.connect()

        try:
            with database.atomic():
                mixnodeFk = Mixnode.get(Mixnode.identityKey == mixnodeid)
                lenghtUser = User.select(User.userid, User.state).where((User.userid == userid) & (User.mixnodeid == mixnodeFk)).count()

                if state:
                    if lenghtUser <= 0:
                        User.create(userid=userid, mixnodeid=mixnodeFk, state=state)
                        logHandler.info(f"New mixnode {mixnodeid}, userid {userid}")
                        return True
                    else:
                        logHandler.error(f"Already exists Mixnode {mixnodeid}, userid {userid}")
                        return False
                else:
                    if lenghtUser >= 1:
                        User.delete().where((User.userid == userid) & (User.mixnodeid == mixnodeFk)).execute()
                        logHandler.info(f"Delete mixnode {mixnodeid}, userid {userid}")
                        return True
                    else:
                        logHandler.error(f"Delete Mixnode {mixnodeid}, userid {userid}")
                        return False
        except IntegrityError as e:
            print(e)
            logHandler.exception(e)
            return False
        except DoesNotExist as e:
            logHandler.exception(e)
            return False
        finally:
            self.close()

    def deleteMixnode(self,identityKey):
        logHandler = logging.getLogger('nym')
        self.connect()

        mixnodeFk = Mixnode.get(Mixnode.identityKey == identityKey)

        logHandler.debug(f"Delete mixnode {identityKey}")
        User.delete().where(User.mixnodeid == mixnodeFk).execute()
        Mixnode.delete().where(Mixnode.id == mixnodeFk).execute()

        self.close()

    def insertMixnode(self, identityKey, status):
        logHandler = logging.getLogger('nym')
        self.connect()

        try:
            with database.atomic():
                Mixnode.insert(identityKey=identityKey, status=status).on_conflict(
                    conflict_target=[Mixnode.identityKey],
                    update={Mixnode.status: status,Mixnode.updated_on: datetime.now()}).execute()
        except IntegrityError as e:
            logHandler.exception(e)
        finally:
            self.close()

    def updateStatus(self, identityKey, status):
        logHandler = logging.getLogger('nym')
        self.connect()

        try:
            with database.atomic():
                Mixnode.update(state=status).where(Mixnode.identityKey == identityKey).execute()
            return True
        except IntegrityError as e:
            print(e)
            logHandler.exception(e)
            return False
        finally:
            self.close()

    def getMixnodes(self):
        self.connect()
        data = [mixnode for mixnode in Mixnode.select(Mixnode.identityKey,Mixnode.status).dicts()]
        self.close()
        return data

    def getMixnodesUser(self,identityKey):
        self.connect()
        mixnodeFk = Mixnode.get(Mixnode.identityKey == identityKey)
        data = [userid for userid in User.select(User.userid,User.state).where((User.mixnodeid == mixnodeFk) & (User.state == True)).dicts()]
        self.close()
        return data

class Mixnode(BaseModel):
    identityKey = CharField(unique=True)
    status = CharField()

    created_on = DateTimeField(default=datetime.now)
    updated_on = DateTimeField(default=datetime.now)


class User(BaseModel):
    userid = CharField()
    mixnodeid = ForeignKeyField(Mixnode, backref='user')
    state = BooleanField()

    created_on = DateTimeField(default=datetime.now)
    updated_on = DateTimeField(default=datetime.now)
